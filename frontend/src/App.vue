<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-brand">
        <div class="navbar-item">
          <img src="/qu-logo-white.png" alt="Qu" style="max-height: 39px; margin-right: 8px;" />
          <strong style="color:white">DataStream Viewer</strong>
        </div>
      </div>
      <div class="navbar-menu">
        <div class="navbar-start">
          <div class="navbar-item">
            <span class="navbar-link is-active">
              <strong><i class="fa-solid fa-stream"></i> Events</strong>
            </span>
          </div>
        </div>
      </div>
    </nav>

    <main class="container">
      <div class="page-header">
        <h1 class="page-title">Event Stream</h1>
        <p class="page-subtitle">Real-time event monitoring and filtering</p>
      </div>

      <div class="control-bar">
        <div class="control-group">
          <div class="form-group">
            <label class="form-label">Company ID</label>
            <input v-model="filters.companyId" placeholder="Filter by company" @input="loadEvents" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Location ID</label>
            <input v-model="filters.locationId" placeholder="Filter by location" @input="loadEvents" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Entity Type</label>
            <input v-model="filters.entityType" placeholder="Filter by entity" @input="loadEvents" class="form-input">
          </div>
        </div>
        <div class="control-actions">
          <button @click="clearFilters" class="btn btn-primary">
            <i class="fa-solid fa-times"></i> Clear
          </button>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Total Events</div>
          <div class="metric-value">{{ total.toLocaleString() }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Current Page</div>
          <div class="metric-value">{{ page }} / {{ pages }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Events per Page</div>
          <div class="metric-value">50</div>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Company</th>
              <th>Location</th>
              <th>Entity</th>
              <th>Event</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="event in events" :key="event._id">
              <td>{{ formatTime(event.timestamp) }}</td>
              <td>{{ event.companyId }}</td>
              <td>{{ event.locationId }}</td>
              <td><span class="badge">{{ event.entityType }}</span></td>
              <td><span class="badge badge-success">{{ event.eventType }}</span></td>
              <td>
                <button @click="viewPayload(event)" class="btn btn-icon">
                  <i class="fa-solid fa-eye"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <button @click="prevPage" :disabled="page === 1" class="btn btn-primary">
          <i class="fa-solid fa-chevron-left"></i> Previous
        </button>
        <span class="pagination-info">Page {{ page }} of {{ pages }}</span>
        <button @click="nextPage" :disabled="page === pages" class="btn btn-primary">
          Next <i class="fa-solid fa-chevron-right"></i>
        </button>
      </div>
    </main>

    <div v-if="selectedEvent" class="modal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Event Details</h2>
          <button class="btn-close" @click="closeModal">
            <i class="fa-solid fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <pre>{{ JSON.stringify(selectedEvent, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const events = ref([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const filters = ref({ companyId: '', locationId: '', entityType: '' })
const selectedEvent = ref(null)
let eventSource = null

const loadEvents = async () => {
  const params = new URLSearchParams({ page: page.value })
  if (filters.value.companyId) params.append('companyId', filters.value.companyId)
  if (filters.value.locationId) params.append('locationId', filters.value.locationId)
  if (filters.value.entityType) params.append('entityType', filters.value.entityType)
  
  const res = await fetch(`/api/events?${params}`)
  const data = await res.json()
  events.value = data.events
  total.value = data.total
  pages.value = data.pages
}

const clearFilters = () => {
  filters.value = { companyId: '', locationId: '', entityType: '' }
  page.value = 1
  loadEvents()
}

const prevPage = () => {
  if (page.value > 1) {
    page.value--
    loadEvents()
  }
}

const nextPage = () => {
  if (page.value < pages.value) {
    page.value++
    loadEvents()
  }
}

const viewPayload = (event) => {
  selectedEvent.value = event
}

const closeModal = () => {
  selectedEvent.value = null
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}

const connectSSE = () => {
  eventSource = new EventSource('/api/events/stream')
  eventSource.onmessage = (e) => {
    const newEvent = JSON.parse(e.data)
    if (page.value === 1 && matchesFilters(newEvent)) {
      events.value.unshift(newEvent)
      if (events.value.length > 50) events.value.pop()
      total.value++
    }
  }
}

const matchesFilters = (event) => {
  if (filters.value.companyId && event.companyId != filters.value.companyId) return false
  if (filters.value.locationId && event.locationId != filters.value.locationId) return false
  if (filters.value.entityType && event.entityType !== filters.value.entityType) return false
  return true
}

onMounted(() => {
  loadEvents()
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>

<style>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');

:root {
  --qu-red-color: #BA353E;
  --qu-light-blue-color: #75ceda;
  --darkgrey: #666;
  --color: #4a4a4a;
  --primary-color: #3b82f6;
  --primary-hover: #2563eb;
  --success-color: #10b981;
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-300: #d1d5db;
  --gray-500: #6b7280;
  --gray-700: #374151;
  --gray-900: #111827;
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1);
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 2rem;
  --transition-base: 0.2s ease;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html {
  background-color: #e8e8e8;
}

body {
  font-family: BlinkMacSystemFont, -apple-system, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", "Helvetica", "Arial", sans-serif;
  line-height: 1.5;
  color: var(--color);
  margin: 0;
  font-weight: 400;
}

.navbar {
  box-shadow: 0 0 15px 0 hsla(0, 0%, 42%, .5);
  position: sticky;
  top: 0;
  height: 56px;
  display: flex;
  background-color: #fff;
  align-items: center;
  z-index: 100;
}

.navbar-brand {
  align-items: center;
  background: var(--qu-red-color);
  display: flex;
  flex-shrink: 0;
  width: 16.66667%;
  padding: 4px 12px;
  height: 100%;
}

.navbar-menu {
  flex-grow: 1;
  display: flex;
}

.navbar-start {
  padding-left: 5px;
  display: flex;
  height: 100%;
}

.navbar-item {
  align-items: center;
  display: flex;
  padding: 8px 12px;
}

.navbar-link {
  border-bottom: .3125rem solid transparent;
  padding: 8px 12px;
  color: var(--darkgrey);
}

.navbar-link.is-active {
  border-bottom-color: var(--qu-red-color);
  color: var(--qu-red-color);
}

.container {
  background-color: white;
  max-width: 1400px;
  margin: 12px auto;
  padding: 20px;
  border-radius: 6px;
  box-shadow: 0 0 15px 0 hsla(0, 0%, 42%, .25);
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--gray-900);
  margin: 0 0 var(--spacing-sm) 0;
}

.page-subtitle {
  color: var(--gray-500);
  font-size: var(--font-size-base);
  margin: 0;
}

.control-bar {
  display: flex;
  align-items: end;
  gap: var(--spacing-xl);
  background: var(--gray-50);
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-xl);
}

.control-group {
  display: flex;
  gap: var(--spacing-md);
  flex: 1;
}

.control-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.form-group {
  flex: 1;
}

.form-label {
  display: block;
  font-weight: 500;
  font-size: var(--font-size-sm);
  color: var(--gray-700);
  margin-bottom: var(--spacing-xs);
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  transition: border-color var(--transition-base);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
  gap: var(--spacing-xs);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-hover);
  transform: translateY(-1px);
}

.btn-icon {
  width: 36px;
  height: 36px;
  padding: 0;
  background-color: var(--gray-100);
  color: var(--gray-700);
}

.btn-icon:hover {
  background-color: var(--gray-200);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.metric-card {
  background: white;
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  border-left: 4px solid var(--primary-color);
}

.metric-label {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  font-weight: 500;
}

.metric-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--gray-900);
}

.table-container {
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  margin-bottom: var(--spacing-xl);
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  background: var(--gray-50);
  padding: var(--spacing-md);
  text-align: left;
  font-weight: 600;
  color: var(--gray-700);
  border-bottom: 1px solid var(--gray-200);
  font-size: var(--font-size-sm);
}

.table td {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--gray-100);
  font-size: var(--font-size-sm);
}

.table tr:hover {
  background: var(--gray-50);
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--gray-100);
  color: var(--gray-700);
}

.badge-success {
  background: #d1fae5;
  color: var(--success-color);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
}

.pagination-info {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: var(--radius-lg);
  max-width: 800px;
  max-height: 80vh;
  overflow: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--gray-200);
}

.modal-header h2 {
  margin: 0;
  font-size: var(--font-size-2xl);
  color: var(--gray-900);
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--gray-500);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
}

.btn-close:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}

.modal-body {
  padding: var(--spacing-lg);
}

pre {
  background: var(--gray-50);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  overflow: auto;
  font-size: 0.875rem;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .control-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-group {
    flex-direction: column;
  }
  
  .navbar-brand {
    width: auto;
  }
}
</style>
