import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import TradeEntry from './pages/TradeEntry';
import PortfolioView from './pages/PortfolioView';
import PortfolioManagement from './pages/PortfolioManagement';
import StockManagement from './pages/StockManagement';
import OptionManagement from './pages/OptionManagement';
import PortfolioAnalytics from './pages/PortfolioAnalytics';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar />
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/trade-entry" element={<TradeEntry />} />
              <Route path="/portfolio/:portfolioName?" element={<PortfolioView />} />
              <Route path="/portfolios" element={<PortfolioManagement />} />
              <Route path="/stocks" element={<StockManagement />} />
              <Route path="/options" element={<OptionManagement />} />
              <Route path="/portfolio-analytics" element={<PortfolioAnalytics />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
