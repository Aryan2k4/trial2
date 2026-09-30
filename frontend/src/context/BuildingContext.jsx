import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { facilityService } from '../services/costService'

const BuildingContext = createContext(null)
const STORAGE_KEY = 'facilityops-building-id'
const FALLBACK_BUILDING = 'BLD-HQ-01'

/**
 * The single source of truth for "which building is the operator looking
 * at right now" — every dashboard page and service call reads
 * buildingId from here instead of hardcoding 'BLD-HQ-01', so switching
 * buildings actually changes what the whole app shows.
 *
 * Fetches the real list of buildings that have data (see
 * GET /api/facility/buildings) rather than hardcoding a static list, so
 * this reflects whatever's actually been ingested.
 */
export function BuildingProvider({ children }) {
  const [buildingId, setBuildingIdState] = useState(() => localStorage.getItem(STORAGE_KEY) || FALLBACK_BUILDING)
  const [buildings, setBuildings] = useState([{ building_id: FALLBACK_BUILDING, is_default: true }])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    facilityService.getBuildings()
      .then((data) => {
        const list = data.buildings?.length ? data.buildings : [{ building_id: FALLBACK_BUILDING, is_default: true }]
        setBuildings(list)
        // If the previously-selected building no longer has any data,
        // fall back to the default rather than showing an empty dashboard.
        setBuildingIdState((current) => (list.some((b) => b.building_id === current) ? current : FALLBACK_BUILDING))
      })
      .catch(() => {}) // keep the single-building fallback list — non-fatal
      .finally(() => setLoading(false))
  }, [])

  const setBuildingId = useCallback((id) => {
    setBuildingIdState(id)
    localStorage.setItem(STORAGE_KEY, id)
  }, [])

  return (
    <BuildingContext.Provider value={{ buildingId, setBuildingId, buildings, loading }}>
      {children}
    </BuildingContext.Provider>
  )
}

export function useBuilding() {
  const ctx = useContext(BuildingContext)
  if (!ctx) throw new Error('useBuilding must be used within BuildingProvider')
  return ctx
}
