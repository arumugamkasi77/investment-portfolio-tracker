import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Chip,
  LinearProgress,
  Tabs,
  Tab,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  CircularProgress,
  IconButton,
  Tooltip,
  Checkbox
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  Assessment as AssessmentIcon,
  PlayArrow as PlayArrowIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import axios from 'axios';
import { portfolioApi } from '../services/api';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

interface Portfolio {
  portfolio_name: string;
  _id?: string;
}

interface ModelStatus {
  symbol: string;
  status: string;
  last_training?: string;
  validation_metrics?: {
    rmse: number;
    mae: number;
    accuracy: number;
  };
  training_history?: {
    loss: number[];
    val_loss: number[];
  };
}

interface PredictionResult {
  symbol: string;
  current_price: number;
  predictions: number[];
  prediction_dates: string[];
  confidence_intervals: {
    lower_68: number[];
    upper_68: number[];
    lower_95: number[];
    upper_95: number[];
  };
  model_accuracy: number;
  prediction_timestamp: string;
}

interface BacktestResult {
  symbol: string;
  backtest_period_days: number;
  metrics: {
    rmse: number;
    mae: number;
    mape: number;
    directional_accuracy: number;
    cumulative_return: number;
  };
  actual_prices: number[];
  predicted_prices: number[];
  backtest_dates: string[];
}

const AIPredictions: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [customSymbol, setCustomSymbol] = useState<string>('');
  const [daysAhead, setDaysAhead] = useState<number>(30);
  const [lookbackDays, setLookbackDays] = useState<number>(60);
  const [epochs, setEpochs] = useState<number>(100);
  const [modelStatuses, setModelStatuses] = useState<ModelStatus[]>([]);
  const [modelInsights, setModelInsights] = useState<{ [key: string]: any }>({});
  const [loadingInsights, setLoadingInsights] = useState<{ [key: string]: boolean }>({});
  const [predictions, setPredictions] = useState<PredictionResult | null>(null);
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [trainingStatus, setTrainingStatus] = useState<{ [key: string]: string }>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);

  // Load portfolios on component mount
  useEffect(() => {
    loadPortfolios();
    loadModelStatuses();
  }, []);

  // Load symbols when portfolio changes or component mounts
  useEffect(() => {
    if (selectedPortfolio) {
      loadPortfolioSymbols(selectedPortfolio);
    }
  }, [selectedPortfolio]);

  const loadPortfolios = async () => {
    try {
      const response = await portfolioApi.getPortfolios();
      setPortfolios(response.data);
      if (response.data.length > 0) {
        setSelectedPortfolio(response.data[0].portfolio_name);
      }
    } catch (error) {
      console.error('Failed to fetch portfolios:', error);
      setMessage({ type: 'error', text: 'Failed to fetch portfolios' });
    }
  };

  const loadModelStatuses = async () => {
    try {
      const response = await api.get('/ai-predictions/models/status');
      const statuses = response.data;
      if (statuses.trained_models) {
        const modelStatusesList = Object.entries(statuses.prediction_history).map(([symbol, data]: [string, any]) => ({
          symbol,
          status: 'trained',
          last_training: data.last_training,
          validation_metrics: data.validation_metrics,
          training_history: data.training_history
        }));
        setModelStatuses(modelStatusesList);
      }
    } catch (error) {
      console.error('Failed to fetch model statuses:', error);
    }
  };

  const loadPortfolioSymbols = async (portfolioName: string) => {
    try {
      const response = await api.post('/ai-predictions/portfolio/symbols', {
        portfolio_name: portfolioName
      });
      setSymbols(response.data.stock_symbols);
      if (response.data.stock_symbols.length > 0) {
        setSelectedSymbol(response.data.stock_symbols[0]);
      }
    } catch (error) {
      console.error('Failed to fetch portfolio symbols:', error);
      setMessage({ type: 'error', text: 'Failed to fetch portfolio symbols' });
    }
  };

  const handlePortfolioChange = (portfolioName: string) => {
    setSelectedPortfolio(portfolioName);
    loadPortfolioSymbols(portfolioName);
  };

  const trainModel = async (symbol: string) => {
    setLoading(true);
    setTrainingStatus(prev => ({ ...prev, [symbol]: 'training' }));

    try {
      const response = await api.post('/ai-predictions/train', {
        symbol,
        lookback_days: lookbackDays,
        epochs
      });

      setMessage({ type: 'success', text: response.data.message });
      setTrainingStatus(prev => ({ ...prev, [symbol]: 'started' }));

      // Start polling for status
      pollTrainingStatus(symbol);

    } catch (error: any) {
      console.error('Training failed:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Training failed' });
      setTrainingStatus(prev => ({ ...prev, [symbol]: 'failed' }));
    } finally {
      setLoading(false);
    }
  };

  const pollTrainingStatus = async (symbol: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/ai-predictions/train/status/${symbol}`);
        if (response.data.status === 'trained') {
          setTrainingStatus(prev => ({ ...prev, [symbol]: 'completed' }));
          loadModelStatuses(); // Refresh model statuses
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Failed to poll training status:', error);
        clearInterval(pollInterval);
      }
    }, 10000); // Poll every 10 seconds
  };

  const bulkTrainPortfolio = async () => {
    if (!selectedPortfolio) return;

    setLoading(true);
    try {
      const response = await api.post('/ai-predictions/portfolio/bulk-train', {
        portfolio_name: selectedPortfolio
      });

      setMessage({ type: 'success', text: response.data.message });

      // Start polling for all symbols
      response.data.symbols_training.forEach((symbol: string) => {
        setTrainingStatus(prev => ({ ...prev, [symbol]: 'started' }));
        pollTrainingStatus(symbol);
      });

    } catch (error: any) {
      console.error('Bulk training failed:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Bulk training failed' });
    } finally {
      setLoading(false);
    }
  };

  const makePrediction = async () => {
    const symbol = customSymbol || selectedSymbol;
    if (!symbol) return;

    setLoading(true);
    try {
      const response = await api.post('/ai-predictions/predict', {
        symbol,
        days_ahead: daysAhead
      });

      setPredictions(response.data);
      setMessage({ type: 'success', text: `Prediction completed for ${symbol}` });

    } catch (error: any) {
      console.error('Prediction failed:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Prediction failed' });
    } finally {
      setLoading(false);
    }
  };

  const runBacktest = async () => {
    const symbol = customSymbol || selectedSymbol;
    if (!symbol) return;

    setLoading(true);
    try {
      const response = await api.post('/ai-predictions/backtest', {
        symbol,
        test_period_days: 90
      });

      setBacktestResults(response.data);
      setMessage({ type: 'success', text: `Backtest completed for ${symbol}` });

    } catch (error: any) {
      console.error('Backtest failed:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Backtest failed' });
    } finally {
      setLoading(false);
    }
  };

  const deleteModel = async (symbol: string) => {
    try {
      await api.delete(`/ai-predictions/models/${symbol}`);
      setMessage({ type: 'success', text: `Model for ${symbol} deleted successfully` });
      loadModelStatuses();
    } catch (error: any) {
      console.error('Failed to delete model:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to delete model' });
    }
  };

  const getTrainingStatusIcon = (status: string) => {
    switch (status) {
      case 'training':
        return <CircularProgress size={20} />;
      case 'started':
        return <CircularProgress size={20} />;
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getTrainingStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'training':
      case 'started':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const fetchModelInsights = async (symbol: string) => {
    try {
      setLoadingInsights(prev => ({ ...prev, [symbol]: true }));
      const response = await api.get(`/ai-predictions/models/insights/${symbol}`);
      if (response.data && !response.data.error) {
        setModelInsights(prev => ({ ...prev, [symbol]: response.data }));
      }
    } catch (error) {
      console.error('Error fetching model insights:', error);
    } finally {
      setLoadingInsights(prev => ({ ...prev, [symbol]: false }));
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <PsychologyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4" gutterBottom>
            AI Stock Price Predictions
          </Typography>
          <Typography variant="body1" color="text.secondary">
            LSTM-based neural networks for intelligent stock price forecasting
          </Typography>
        </Box>
      </Box>

      {message && (
        <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          <AlertTitle>{message.type === 'success' ? 'Success' : message.type === 'error' ? 'Error' : 'Info'}</AlertTitle>
          {message.text}
        </Alert>
      )}

      {symbols.length === 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <AlertTitle>Getting Started</AlertTitle>
          Welcome to AI Stock Price Predictions! To begin, select a portfolio from the left panel to see available stocks for training LSTM models.
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Model Training" icon={<PlayArrowIcon />} />
        <Tab label="Price Predictions" icon={<AssessmentIcon />} />
        <Tab label="Backtesting" icon={<AssessmentIcon />} />
        <Tab label="Model Management" icon={<AnalyticsIcon />} />
        <Tab label="Model Insights" icon={<InfoIcon />} />
      </Tabs>

      {/* Enhanced Features Info Box */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>🚀 Enhanced AI Model Features</AlertTitle>
        <Typography variant="body2">
          <strong>New Data Sources:</strong> VIX volatility index, sector ETF data, S&P 500 correlation, extended historical data (max available)
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          <strong>Improved Architecture:</strong> 4-layer LSTM with recurrent dropout, L2 regularization, enhanced training with learning rate scheduling
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          <strong>Expected Improvement:</strong> 8-15% accuracy boost with these enhancements
        </Typography>
      </Alert>

      {/* Model Training Tab */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
          <Box>
            <Card>
              <CardHeader title="Portfolio Integration" />
              <CardContent>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Select Portfolio</InputLabel>
                  <Select
                    value={selectedPortfolio}
                    onChange={(e) => handlePortfolioChange(e.target.value)}
                    label="Select Portfolio"
                  >
                    {portfolios.map((portfolio) => (
                      <MenuItem key={portfolio.portfolio_name} value={portfolio.portfolio_name}>
                        {portfolio.portfolio_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {symbols.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Available Stocks: {symbols.length}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      {symbols.map((symbol) => (
                        <Chip
                          key={symbol}
                          label={symbol}
                          variant={selectedSymbol === symbol ? 'filled' : 'outlined'}
                          onClick={() => setSelectedSymbol(symbol)}
                          clickable
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                <Button
                  variant="contained"
                  onClick={bulkTrainPortfolio}
                  disabled={!selectedPortfolio || symbols.length === 0 || loading}
                  startIcon={<PlayArrowIcon />}
                  fullWidth
                >
                  Train All Portfolio Models
                </Button>

                <Box sx={{ mt: 2, p: 2, bgcolor: 'blue.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom color="primary">
                    💡 How It Works
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    1. <strong>Select Portfolio:</strong> Choose from your existing portfolios
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    2. <strong>View Stocks:</strong> See all available stocks as clickable chips
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    3. <strong>Bulk Train:</strong> Train LSTM models for all stocks simultaneously
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    4. <strong>Monitor Progress:</strong> Track training status in real-time
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box>
            <Card>
              <CardHeader title="Custom Model Training" />
              <CardContent>
                {symbols.length === 0 ? (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <AlertTitle>Portfolio Required</AlertTitle>
                    To see available stocks, please select a portfolio in the left panel first.
                  </Alert>
                ) : (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <AlertTitle>Portfolio Loaded</AlertTitle>
                    {symbols.length} stocks available from portfolio "{selectedPortfolio}"
                  </Alert>
                )}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Choose Training Method:
                  </Typography>

                  {/* Option 1: Select from Portfolio Stocks */}
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Select Stocks from Portfolio</InputLabel>
                    <Select
                      multiple
                      value={selectedSymbols}
                      onChange={(e) => {
                        const selected = typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value;
                        setSelectedSymbols(selected);
                        setSelectedSymbol(''); // Clear single selection
                        setCustomSymbol(''); // Clear custom symbol when portfolio stocks are selected
                      }}
                      label="Select Stocks from Portfolio"
                      disabled={symbols.length === 0}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip key={value} label={value} size="small" />
                          ))}
                        </Box>
                      )}
                    >
                      {symbols.map((symbol) => (
                        <MenuItem key={symbol} value={symbol}>
                          <Checkbox checked={selectedSymbols.indexOf(symbol) > -1} />
                          <ListItemText primary={symbol} />
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Selected: {selectedSymbols.length > 0 ? selectedSymbols.join(', ') : 'None'}
                    </Typography>
                    {selectedSymbols.length > 0 && (
                      <Button
                        size="small"
                        onClick={() => setSelectedSymbols([])}
                        sx={{ mr: 1 }}
                      >
                        Clear Selection
                      </Button>
                    )}
                    {symbols.length > 0 && (
                      <Button
                        size="small"
                        onClick={() => setSelectedSymbols(symbols)}
                      >
                        Select All
                      </Button>
                    )}
                  </Box>

                  {symbols.length === 0 && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontStyle: 'italic' }}>
                      💡 Tip: Select a portfolio in the left panel to see available stocks
                    </Typography>
                  )}

                  {/* Option 2: Enter Custom Symbol */}
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    OR enter a custom stock symbol:
                  </Typography>
                  <TextField
                    fullWidth
                    label="Custom Stock Symbol"
                    value={customSymbol}
                    onChange={(e) => {
                      setCustomSymbol(e.target.value.toUpperCase());
                      setSelectedSymbol(''); // Clear portfolio selection when custom symbol is entered
                    }}
                    placeholder="e.g., AAPL, MSFT, TSLA"
                    sx={{ mb: 2 }}
                  />
                </Box>

                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 2 }}>
                  <TextField
                    fullWidth
                    label="Lookback Days"
                    type="number"
                    value={lookbackDays}
                    onChange={(e) => setLookbackDays(Number(e.target.value))}
                    inputProps={{ min: 30, max: 120 }}
                    helperText="Historical days for prediction context"
                  />
                  <TextField
                    fullWidth
                    label="Training Epochs"
                    type="number"
                    value={epochs}
                    onChange={(e) => setEpochs(Number(e.target.value))}
                    inputProps={{ min: 50, max: 200 }}
                    helperText="Training iterations (early stopping enabled)"
                  />
                </Box>

                <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom color="primary">
                    🧠 LSTM Model Features
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    • <strong>Data:</strong> 5 years of OHLCV + 17+ technical indicators
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    • <strong>Architecture:</strong> 3-layer LSTM with dropout (100 units each)
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    • <strong>Validation:</strong> 80% training, 20% validation with early stopping
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • <strong>Features:</strong> SMA, EMA, RSI, MACD, Bollinger Bands, Volume, Volatility
                  </Typography>
                </Box>

                <Button
                  variant="contained"
                  onClick={() => {
                    if (selectedSymbols.length > 0) {
                      // Train multiple selected stocks
                      selectedSymbols.forEach(symbol => trainModel(symbol));
                    } else if (selectedSymbol || customSymbol) {
                      // Train single stock
                      trainModel(selectedSymbol || customSymbol);
                    }
                  }}
                  disabled={(!selectedSymbols.length && !selectedSymbol && !customSymbol) || loading}
                  startIcon={<PlayArrowIcon />}
                  fullWidth
                >
                  {selectedSymbols.length > 0
                    ? `Train ${selectedSymbols.length} Selected Model${selectedSymbols.length > 1 ? 's' : ''}`
                    : 'Train Model'
                  }
                </Button>

                <Box sx={{ mt: 2, p: 2, bgcolor: 'green.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    🎯 Training Options
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    • <strong>Multiple Portfolio Stocks:</strong> Select one or more stocks to train simultaneously
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    • <strong>Custom Symbol:</strong> Train on any stock symbol you're interested in
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    • <strong>Bulk Training:</strong> Train multiple models at once for efficiency
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • <strong>Note:</strong> Portfolio stocks have more data available for better training
                  </Typography>
                </Box>

                {selectedSymbols.length > 0 && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'blue.50', borderRadius: 1 }}>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      🚀 Bulk Training Ready
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • <strong>Selected Stocks:</strong> {selectedSymbols.join(', ')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • <strong>Estimated Time:</strong> {selectedSymbols.length * 10} minutes total
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • <strong>Models:</strong> Each stock will get its own trained LSTM model
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Card>
              <CardHeader
                title="Training Status"
                action={
                  Object.keys(trainingStatus).length > 0 && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        {Object.values(trainingStatus).filter(s => s === 'completed').length} / {Object.keys(trainingStatus).length} completed
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(Object.values(trainingStatus).filter(s => s === 'completed').length / Object.keys(trainingStatus).length) * 100}
                        sx={{ width: 100 }}
                      />
                    </Box>
                  )
                }
              />
              <CardContent>
                {Object.keys(trainingStatus).length === 0 ? (
                  <Typography color="text.secondary">No training in progress</Typography>
                ) : (
                  <List>
                    {Object.entries(trainingStatus).map(([symbol, status]) => (
                      <ListItem key={symbol}>
                        <ListItemIcon>
                          {getTrainingStatusIcon(status)}
                        </ListItemIcon>
                        <ListItemText
                          primary={symbol}
                          secondary={`Status: ${status}`}
                        />
                        <Chip
                          label={status}
                          color={getTrainingStatusColor(status) as any}
                          size="small"
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Card>
              <CardHeader title="🎯 Training Tips & Best Practices" />
              <CardContent>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                  <Box>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      📈 For Best Results:
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • Start with portfolio stocks (more data available)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • Use default parameters for first training
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • Train during market hours for fresh data
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • Monitor validation metrics for overfitting
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      ⏱️ Training Time:
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • Single model: 5-15 minutes
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • Portfolio models: 10-30 minutes total
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • Depends on data size and epochs
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • Early stopping may reduce actual time
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </TabPanel>

      {/* Price Predictions Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
          <Box>
            <Card>
              <CardHeader title="Prediction Settings" />
              <CardContent>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Choose Stock for Prediction:
                  </Typography>

                  {/* Option 1: Select from Portfolio Stocks */}
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Select from Portfolio</InputLabel>
                    <Select
                      value={selectedSymbol}
                      onChange={(e) => {
                        setSelectedSymbol(e.target.value);
                        setCustomSymbol(''); // Clear custom symbol when portfolio stock is selected
                      }}
                      label="Select from Portfolio"
                    >
                      <MenuItem value="">
                        <em>Choose a stock from your portfolio</em>
                      </MenuItem>
                      {symbols.map((symbol) => (
                        <MenuItem key={symbol} value={symbol}>
                          {symbol}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {/* Option 2: Enter Custom Symbol */}
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    OR enter a custom stock symbol:
                  </Typography>
                  <TextField
                    fullWidth
                    label="Custom Stock Symbol"
                    value={customSymbol}
                    onChange={(e) => {
                      setCustomSymbol(e.target.value.toUpperCase());
                      setSelectedSymbol(''); // Clear portfolio selection when custom symbol is entered
                    }}
                    placeholder="e.g., AAPL, MSFT, TSLA"
                    sx={{ mb: 2 }}
                  />
                </Box>

                <TextField
                  fullWidth
                  label="Days to Predict"
                  type="number"
                  value={daysAhead}
                  onChange={(e) => setDaysAhead(Number(e.target.value))}
                  inputProps={{ min: 7, max: 90 }}
                  sx={{ mb: 2 }}
                />

                <Button
                  variant="contained"
                  onClick={makePrediction}
                  disabled={(!selectedSymbol && !customSymbol) || loading}
                  startIcon={<AssessmentIcon />}
                  fullWidth
                >
                  Generate Prediction
                </Button>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ gridColumn: { xs: '1', md: 'span 2' } }}>
            {predictions ? (
              <Card>
                <CardHeader
                  title={`Price Prediction: ${predictions.symbol}`}
                  subheader={`Current Price: ${formatPrice(predictions.current_price)} | Model Accuracy: ${formatPercentage(predictions.model_accuracy)}`}
                />
                <CardContent>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>Predicted Prices (Next {daysAhead} Days)</Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1 }}>
                      {predictions.predictions.map((price, index) => (
                        <Paper key={index} sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            {predictions.prediction_dates[index]}
                          </Typography>
                          <Typography variant="h6" color="primary">
                            {formatPrice(price)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ±{formatPrice((predictions.confidence_intervals.upper_68[index] - predictions.confidence_intervals.lower_68[index]) / 2)}
                          </Typography>
                        </Paper>
                      ))}
                    </Box>
                  </Box>

                  <Box>
                    <Typography variant="h6" gutterBottom>Confidence Intervals</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      68% confidence: {formatPrice(predictions.confidence_intervals.upper_68[0] - predictions.confidence_intervals.lower_68[0])} range
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      95% confidence: {formatPrice(predictions.confidence_intervals.upper_95[0] - predictions.confidence_intervals.lower_95[0])} range
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 8 }}>
                  <AssessmentIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No Predictions Yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Select a stock and generate predictions to see results
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Box>
        </Box>
      </TabPanel>

      {/* Backtesting Tab */}
      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
          <Box>
            <Card>
              <CardHeader title="Backtest Settings" />
              <CardContent>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Choose Stock for Backtesting:
                  </Typography>

                  {/* Option 1: Select from Portfolio Stocks */}
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Select from Portfolio</InputLabel>
                    <Select
                      value={selectedSymbol}
                      onChange={(e) => {
                        setSelectedSymbol(e.target.value);
                        setCustomSymbol(''); // Clear custom symbol when portfolio stock is selected
                      }}
                      label="Select from Portfolio"
                    >
                      <MenuItem value="">
                        <em>Choose a stock from your portfolio</em>
                      </MenuItem>
                      {symbols.map((symbol) => (
                        <MenuItem key={symbol} value={symbol}>
                          {symbol}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {/* Option 2: Enter Custom Symbol */}
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    OR enter a custom stock symbol:
                  </Typography>
                  <TextField
                    fullWidth
                    label="Custom Stock Symbol"
                    value={customSymbol}
                    onChange={(e) => {
                      setCustomSymbol(e.target.value.toUpperCase());
                      setSelectedSymbol(''); // Clear portfolio selection when custom symbol is entered
                    }}
                    placeholder="e.g., AAPL, MSFT, TSLA"
                    sx={{ mb: 2 }}
                  />
                </Box>

                <Button
                  variant="contained"
                  onClick={runBacktest}
                  disabled={(!selectedSymbol && !customSymbol) || loading}
                  startIcon={<AssessmentIcon />}
                  fullWidth
                >
                  Run Backtest
                </Button>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ gridColumn: { xs: '1', md: 'span 2' } }}>
            {backtestResults ? (
              <Card>
                <CardHeader
                  title={`Backtest Results: ${backtestResults.symbol}`}
                  subheader={`Test Period: ${backtestResults.backtest_period_days} days`}
                />
                <CardContent>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 2, mb: 3 }}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6" color="primary">
                        {formatPrice(backtestResults.metrics.rmse)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        RMSE
                      </Typography>
                    </Paper>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6" color="primary">
                        {formatPrice(backtestResults.metrics.mae)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        MAE
                      </Typography>
                    </Paper>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6" color="primary">
                        {formatPercentage(backtestResults.metrics.directional_accuracy)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Directional Accuracy
                      </Typography>
                    </Paper>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6" color="primary">
                        {formatPercentage(backtestResults.metrics.cumulative_return)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Cumulative Return
                      </Typography>
                    </Paper>
                  </Box>

                  <Box>
                    <Typography variant="h6" gutterBottom>Performance Analysis</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • Mean Absolute Percentage Error: {formatPercentage(backtestResults.metrics.mape)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • The model correctly predicted price direction {formatPercentage(backtestResults.metrics.directional_accuracy)} of the time
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • Overall model performance: {backtestResults.metrics.rmse < 5 ? 'Excellent' : backtestResults.metrics.rmse < 10 ? 'Good' : 'Needs Improvement'}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 8 }}>
                  <AssessmentIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No Backtest Results
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Select a stock and run backtesting to see performance metrics
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Box>
        </Box>
      </TabPanel>

      {/* Model Management Tab */}
      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardHeader
            title="Trained Models"
            action={
              <Button
                startIcon={<RefreshIcon />}
                onClick={loadModelStatuses}
                variant="outlined"
              >
                Refresh
              </Button>
            }
          />
          <CardContent>
            {modelStatuses.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <AnalyticsIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No Trained Models
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Train models for your stocks to start making predictions
                </Typography>
              </Box>
            ) : (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                {modelStatuses.map((model) => (
                  <Box key={model.symbol}>
                    <Paper sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box>
                          <Typography variant="h6">{model.symbol}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Last trained: {model.last_training ? formatDate(model.last_training) : 'Unknown'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="Delete Model">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => deleteModel(model.symbol)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>

                      {model.validation_metrics && (
                        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1, mb: 2 }}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">RMSE</Typography>
                            <Typography variant="body2">{formatPrice(model.validation_metrics.rmse)}</Typography>
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">MAE</Typography>
                            <Typography variant="body2">{formatPrice(model.validation_metrics.mae)}</Typography>
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">Accuracy</Typography>
                            <Typography variant="body2">{formatPercentage(model.validation_metrics.accuracy)}</Typography>
                          </Box>
                        </Box>
                      )}

                      <Chip
                        label="Trained"
                        color="success"
                        size="small"
                        icon={<CheckCircleIcon />}
                      />
                    </Paper>
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Model Insights Tab */}
      <TabPanel value={tabValue} index={4}>
        <Card>
          <CardHeader
            title="Model Insights & Analytics"
            subheader="Comprehensive analysis of your trained models with actionable recommendations"
          />
          <CardContent>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Get detailed insights into your model performance, understand feature importance, and receive
              personalized recommendations to improve accuracy. This analysis helps you optimize your AI models
              for better stock price predictions.
            </Typography>

            {modelStatuses.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <InfoIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No Trained Models to Analyze
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Train models first to see detailed insights and recommendations.
                </Typography>
              </Box>
            ) : (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
                {modelStatuses.map((model) => {
                  const insights = modelInsights[model.symbol];
                  const isLoading = loadingInsights[model.symbol];

                  return (
                    <Paper key={model.symbol} sx={{ p: 3, position: 'relative' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" gutterBottom>{model.symbol}</Typography>
                        <Button
                          size="small"
                          onClick={() => fetchModelInsights(model.symbol)}
                          disabled={isLoading}
                          startIcon={isLoading ? <CircularProgress size={16} /> : <InfoIcon />}
                        >
                          {insights ? 'Refresh Insights' : 'Get Insights'}
                        </Button>
                      </Box>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Last Training: {model.last_training ? formatDate(model.last_training) : 'Never'}
                      </Typography>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Status: <Chip label={model.status} color={getTrainingStatusColor(model.status) as any} size="small" />
                      </Typography>

                      {model.validation_metrics && (
                        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2, mb: 3 }}>
                          <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                            <Typography variant="caption" color="text.secondary">RMSE</Typography>
                            <Typography variant="h6">{formatPrice(model.validation_metrics.rmse)}</Typography>
                          </Box>
                          <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                            <Typography variant="caption" color="text.secondary">MAE</Typography>
                            <Typography variant="h6">{formatPrice(model.validation_metrics.mae)}</Typography>
                          </Box>
                          <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                            <Typography variant="caption" color="text.secondary">Accuracy</Typography>
                            <Typography variant="h6">{formatPercentage(model.validation_metrics.accuracy)}</Typography>
                          </Box>
                        </Box>
                      )}

                      {insights && !insights.error ? (
                        <Box>
                          {/* Performance Analysis */}
                          {insights.performance_analysis && (
                            <Box sx={{ mb: 3 }}>
                              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                Performance Analysis
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Chip
                                  label={insights.performance_analysis.performance_rating}
                                  color={insights.performance_analysis.rating_color as any}
                                  size="small"
                                  sx={{ mr: 1 }}
                                />
                                <Typography variant="body2">
                                  {insights.performance_analysis.accuracy_interpretation}
                                </Typography>
                              </Box>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {insights.performance_analysis.rmse_interpretation}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {insights.performance_analysis.mape_interpretation}
                              </Typography>
                            </Box>
                          )}

                          {/* Feature Insights */}
                          {insights.feature_insights && !insights.feature_insights.error && (
                            <div style={{ marginBottom: '24px' }}>
                              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                Key Features
                              </Typography>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {Object.entries(insights.feature_insights).map(([category, features]) => (
                                  <div key={category}>
                                    <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                                      {category.replace('_', ' ')}:
                                    </Typography>
                                    <div style={{ marginLeft: '8px' }}>
                                      {Object.entries(features as any).map(([feature, description]) => (
                                        <div key={feature} style={{ fontSize: '0.8rem', marginBottom: '4px' }}
                                          dangerouslySetInnerHTML={{
                                            __html: `• <strong>${feature}:</strong> ${description}`
                                          }}
                                        />
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Improvement Recommendations */}
                          {insights.improvement_recommendations && insights.improvement_recommendations.length > 0 && (
                            <Box>
                              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                Improvement Recommendations
                              </Typography>
                              <List dense>
                                {insights.improvement_recommendations.map((rec: string, index: number) => (
                                  <ListItem key={index} sx={{ py: 0.5 }}>
                                    <ListItemIcon>
                                      <InfoIcon color="info" fontSize="small" />
                                    </ListItemIcon>
                                    <ListItemText primary={rec} />
                                  </ListItem>
                                ))}
                              </List>
                            </Box>
                          )}
                        </Box>
                      ) : insights && insights.error ? (
                        <Alert severity="error" sx={{ mt: 2 }}>
                          {insights.error}
                        </Alert>
                      ) : null}
                    </Paper>
                  );
                })}
              </Box>
            )}
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

// TabPanel component
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ai-predictions-tabpanel-${index}`}
      aria-labelledby={`ai-predictions-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

export default AIPredictions;
