import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import PortfolioManagement from './pages/PortfolioManagement';
import PortfolioView from './pages/PortfolioView';
import TradeEntry from './pages/TradeEntry';
import StockManagement from './pages/StockManagement';
import OptionManagement from './pages/OptionManagement';
import PortfolioAnalytics from './pages/PortfolioAnalytics';

import { AutoRefreshProvider } from './contexts/AutoRefreshContext';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AutoRefreshProvider>
        <Router>
          <Navbar />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/portfolio-management" element={<PortfolioManagement />} />
            <Route path="/portfolio-view" element={<PortfolioView />} />
            <Route path="/trade-entry" element={<TradeEntry />} />
            <Route path="/stock-management" element={<StockManagement />} />
            <Route path="/option-management" element={<OptionManagement />} />
            <Route path="/portfolio-analytics" element={<PortfolioAnalytics />} />

          </Routes>
        </Router>
      </AutoRefreshProvider>
    </ThemeProvider>
  );
}

export default App;