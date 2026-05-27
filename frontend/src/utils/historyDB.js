const DB_NAME = 'HistoryRecordsDB'
const DB_VERSION = 1
const STORE_NAME = 'records'

let dbInstance = null

function openDB() {
  if (dbInstance) return Promise.resolve(dbInstance)
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = (e) => {
      const db = e.target.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true })
        store.createIndex('moduleName', 'moduleName', { unique: false })
        store.createIndex('savedAt', 'savedAt', { unique: false })
        store.createIndex('module_time', ['moduleName', 'savedAt'], { unique: false })
      }
    }
    request.onsuccess = (e) => {
      dbInstance = e.target.result
      resolve(dbInstance)
    }
    request.onerror = (e) => {
      reject(e.target.error)
    }
  })
}

export async function saveRecord(moduleName, content) {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const record = {
      moduleName,
      content,
      savedAt: new Date().toISOString(),
      contentHash: simpleHash(content)
    }
    const req = store.add(record)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function getRecordsByModule(moduleName) {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const index = store.index('moduleName')
    const req = index.getAll(moduleName)
    req.onsuccess = () => {
      const records = req.result.sort((a, b) => new Date(b.savedAt) - new Date(a.savedAt))
      resolve(records)
    }
    req.onerror = () => reject(req.error)
  })
}

export async function getRecordById(id) {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const req = store.get(id)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function getLastRecordHash(moduleName) {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const index = store.index('moduleName')
    const req = index.openCursor(moduleName, 'prev')
    req.onsuccess = (e) => {
      const cursor = e.target.result
      if (cursor) {
        resolve(cursor.value.contentHash || null)
      } else {
        resolve(null)
      }
    }
    req.onerror = () => reject(req.error)
  })
}

export async function getAllModuleNames() {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const req = store.getAll()
    req.onsuccess = () => {
      const names = [...new Set(req.result.map(r => r.moduleName))]
      resolve(names)
    }
    req.onerror = () => reject(req.error)
  })
}

export async function deleteRecord(id) {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const req = store.delete(id)
    req.onsuccess = () => resolve()
    req.onerror = () => reject(req.error)
  })
}

export function simpleHash(str) {
  if (!str) return 0
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash |= 0
  }
  return hash
}

export function isIndexedDBAvailable() {
  try {
    return typeof indexedDB !== 'undefined'
  } catch {
    return false
  }
}
