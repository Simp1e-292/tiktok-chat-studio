// ============================================================================
// db.js — IndexedDB Storage Engine cho TikTok Chat Studio
// Thay thế localStorage để lưu trữ KHÔNG GIỚI HẠN nhân vật & avatar
// ============================================================================

const DB_NAME = 'TikTokChatStudio';
const DB_VERSION = 1;
const STORE_CHARACTERS = 'characters';
const STORE_SCENARIOS = 'scenarios';
const STORE_SETTINGS = 'settings';

let _db = null;

/**
 * Mở hoặc khởi tạo database IndexedDB
 * @returns {Promise<IDBDatabase>}
 */
function openDB() {
    if (_db) return Promise.resolve(_db);

    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            // Store cho nhân vật — key là id
            if (!db.objectStoreNames.contains(STORE_CHARACTERS)) {
                db.createObjectStore(STORE_CHARACTERS, { keyPath: 'id' });
            }

            // Store cho kịch bản — key là scenarioKey
            if (!db.objectStoreNames.contains(STORE_SCENARIOS)) {
                db.createObjectStore(STORE_SCENARIOS, { keyPath: 'key' });
            }

            // Store cho cài đặt chung — key-value đơn giản
            if (!db.objectStoreNames.contains(STORE_SETTINGS)) {
                db.createObjectStore(STORE_SETTINGS, { keyPath: 'key' });
            }
        };

        request.onsuccess = (event) => {
            _db = event.target.result;
            resolve(_db);
        };

        request.onerror = (event) => {
            console.error('IndexedDB open error:', event.target.error);
            reject(event.target.error);
        };
    });
}

// ============================================================================
// GENERIC CRUD OPERATIONS
// ============================================================================

/**
 * Ghi một item vào store (put = upsert)
 */
function dbPut(storeName, item) {
    return openDB().then(db => {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.put(item);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    });
}

/**
 * Đọc một item theo key
 */
function dbGet(storeName, key) {
    return openDB().then(db => {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    });
}

/**
 * Đọc tất cả items trong store
 */
function dbGetAll(storeName) {
    return openDB().then(db => {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    });
}

/**
 * Xóa một item theo key
 */
function dbDelete(storeName, key) {
    return openDB().then(db => {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.delete(key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    });
}

/**
 * Xóa tất cả items trong store
 */
function dbClear(storeName) {
    return openDB().then(db => {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    });
}

// ============================================================================
// CHARACTER-SPECIFIC HELPERS
// ============================================================================

/**
 * Lưu toàn bộ roster nhân vật vào IndexedDB
 * @param {Array} roster - Mảng nhân vật
 */
async function saveCharactersToIndexedDB(roster) {
    // Xóa hết rồi ghi mới (đảm bảo đồng bộ với mảng in-memory)
    await dbClear(STORE_CHARACTERS);
    for (const char of roster) {
        await dbPut(STORE_CHARACTERS, char);
    }
}

/**
 * Nạp toàn bộ roster nhân vật từ IndexedDB
 * @returns {Promise<Array>}
 */
async function loadCharactersFromIndexedDB() {
    const chars = await dbGetAll(STORE_CHARACTERS);
    return chars && chars.length > 0 ? chars : null;
}

/**
 * Migration: Chuyển dữ liệu từ localStorage sang IndexedDB (chạy 1 lần)
 */
async function migrateFromLocalStorage() {
    const existingChars = await loadCharactersFromIndexedDB();
    if (existingChars && existingChars.length > 0) {
        // Đã có dữ liệu trong IndexedDB — không cần migrate
        return existingChars;
    }

    // Thử lấy từ localStorage cũ
    let oldData = null;
    try {
        const raw = localStorage.getItem('tiktok_studio_characters_v2') 
                 || localStorage.getItem('tiktok_studio_characters');
        if (raw) {
            oldData = JSON.parse(raw);
        }
    } catch (e) {
        console.warn('Migration: Cannot read localStorage:', e);
    }

    if (oldData && oldData.length > 0) {
        console.log(`Migration: Moving ${oldData.length} characters from localStorage to IndexedDB...`);
        await saveCharactersToIndexedDB(oldData);
        // Xóa dữ liệu cũ khỏi localStorage để giải phóng dung lượng
        try {
            localStorage.removeItem('tiktok_studio_characters_v2');
            localStorage.removeItem('tiktok_studio_characters');
        } catch (e) { /* ignore */ }
        return oldData;
    }

    return null; // Không có dữ liệu cũ
}

// ============================================================================
// SCENARIO HELPERS
// ============================================================================

/**
 * Lưu một kịch bản vào IndexedDB
 */
async function saveScenarioToIndexedDB(key, scenarioData) {
    await dbPut(STORE_SCENARIOS, { key, ...scenarioData });
}

/**
 * Nạp tất cả kịch bản từ IndexedDB
 */
async function loadScenariosFromIndexedDB() {
    const items = await dbGetAll(STORE_SCENARIOS);
    if (!items || items.length === 0) return null;
    const result = {};
    for (const item of items) {
        const { key, ...data } = item;
        result[key] = data;
    }
    return result;
}

// ============================================================================
// SETTINGS HELPERS
// ============================================================================

async function saveSetting(key, value) {
    await dbPut(STORE_SETTINGS, { key, value });
}

async function loadSetting(key) {
    const item = await dbGet(STORE_SETTINGS, key);
    return item ? item.value : null;
}
