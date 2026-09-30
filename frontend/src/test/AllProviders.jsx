import { ThemeProvider } from '../context/ThemeContext'
import { BuildingProvider } from '../context/BuildingContext'

/**
 * Every dashboard page (and ForecastCard) now reads buildingId from
 * BuildingContext, same as ThemeContext — tests need both providers
 * present or components using useBuilding()/useTheme() throw.
 */
export function AllProviders({ children }) {
  return (
    <ThemeProvider>
      <BuildingProvider>{children}</BuildingProvider>
    </ThemeProvider>
  )
}
