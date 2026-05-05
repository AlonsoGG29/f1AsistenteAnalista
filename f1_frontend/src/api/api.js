import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 15000,
});

// ── Drivers ─────────────────────────────────────────────────────────────────
export const getDrivers = (params = {}) =>
  API.get('/api/drivers', { params }).then(r => r.data);

export const getDriver = (id) =>
  API.get(`/api/drivers/${id}`).then(r => r.data);

// ── Constructors ─────────────────────────────────────────────────────────────
export const getConstructors = (params = {}) =>
  API.get('/api/constructors', { params }).then(r => r.data);

export const getConstructor = (id) =>
  API.get(`/api/constructors/${id}`).then(r => r.data);

// ── Circuits ─────────────────────────────────────────────────────────────────
export const getCircuits = (params = {}) =>
  API.get('/api/circuits', { params }).then(r => r.data);

export const getCircuitStats = (id) =>
  API.get(`/api/analysis/circuits/${id}/stats`).then(r => r.data);

// ── Races ────────────────────────────────────────────────────────────────────
export const getRaces = (params = {}) =>
  API.get('/api/races', { params }).then(r => r.data);

export const getRaceResults = (raceId) =>
  API.get(`/api/races/${raceId}/results`).then(r => r.data);

// ── Standings ────────────────────────────────────────────────────────────────
export const getDriverStandings = (year, afterRound) =>
  API.get(`/api/standings/drivers/${year}`, { params: afterRound ? { after_round: afterRound } : {} }).then(r => r.data);

export const getConstructorStandings = (year) =>
  API.get(`/api/standings/constructors/${year}`).then(r => r.data);

// ── Analysis ─────────────────────────────────────────────────────────────────
export const getRaceLapTimes = (raceId, driverIds) =>
  API.get(`/api/analysis/races/${raceId}/lap-times`, {
    params: driverIds ? { driver_ids: driverIds.join(',') } : {}
  }).then(r => r.data);

export const getRacePitStops = (raceId) =>
  API.get(`/api/analysis/races/${raceId}/pit-stops`).then(r => r.data);

export const getDriverSeasonStats = (driverId, year) =>
  API.get(`/api/analysis/drivers/${driverId}/season-stats`, {
    params: year ? { year } : {}
  }).then(r => r.data);

export const getConstructorSeasonStats = (constructorId, year) =>
  API.get(`/api/analysis/constructors/${constructorId}/season-stats`, {
    params: year ? { year } : {}
  }).then(r => r.data);

export const getHeadToHead = (driverA, driverB, year) =>
  API.get('/api/analysis/head-to-head', {
    params: { driver_a: driverA, driver_b: driverB, ...(year ? { year } : {}) }
  }).then(r => r.data);

export const getDriverLapProgression = (driverId, year) =>
  API.get(`/api/analysis/drivers/${driverId}/lap-progression/${year}`).then(r => r.data);

// ── ML Predictions ───────────────────────────────────────────────────────────
export const getMLStatus = () =>
  API.get('/api/predict/status').then(r => r.data);

export const predictSafetyCar = (payload) =>
  API.post('/api/predict/safety-car', payload).then(r => r.data);

export const predictMechanicalFailure = (payload) =>
  API.post('/api/predict/mechanical-failure', payload).then(r => r.data);

export const predictPodium = (payload) =>
  API.post('/api/predict/podium', payload).then(r => r.data);

export const getFeatureImportance = (model) =>
  API.get(`/api/predict/feature-importance/${model}`).then(r => r.data);

// ── Health ───────────────────────────────────────────────────────────────────
export const getHealth = () =>
  API.get('/health').then(r => r.data);

export default API;
