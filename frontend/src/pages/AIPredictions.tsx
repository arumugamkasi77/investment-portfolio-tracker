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
  Grid,
  Chip,
  LinearProgress,
  Tabs,
  Tab,
  Alert,
  AlertTitle,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Timeline as TimelineIcon,
  ShowChart as ShowChartIcon,
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
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [customSymbol, setCustomSymbol] = useState<string>('');
  const [daysAhead, setDaysAhead] = useState<number>(30);
  const [lookbackDays, setLookbackDays] = useState<number>(60);
  const [epochs, setEpochs] = useState<number>(100);
  const [modelStatuses, setModelStatuses] = useState<ModelStatus[]>([]);
  const [predictions, setPredictions] = useState<PredictionResult | null>(null);
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [trainingStatus, setTrainingStatus] = useState<{[key: string]: string}>({});
  const [message, setMessage] = useState<{type: 'success' | 'error' | 'info', text: string} | null>(null);

  // Load portfolios on component mount
  useEffect(() => {
    loadPortfolios();
    loadModelStatuses();
  }, []);

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

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Model Training" icon={<PlayArrowIcon />} />
        <Tab label="Price Predictions" icon={<TrendingUpIcon />} />
        <Tab label="Backtesting" icon={<AssessmentIcon />} />
        <Tab label="Model Management" icon={<AnalyticsIcon />} />
      </Tabs>

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
              </CardContent>
            </Card>
          </Box>

          <Box>
            <Card>
              <CardHeader title="Custom Model Training" />
              <CardContent>
                <TextField
                  fullWidth
                  label="Stock Symbol"
                  value={customSymbol}
                  onChange={(e) => setCustomSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL, MSFT"
                  sx={{ mb: 2 }}
                />

                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 2 }}>
                  <TextField
                    fullWidth
                    label="Lookback Days"
                    type="number"
                    value={lookbackDays}
                    onChange={(e) => setLookbackDays(Number(e.target.value))}
                    inputProps={{ min: 30, max: 120 }}
                  />
                  <TextField
                    fullWidth
                    label="Training Epochs"
                    type="number"
                    value={epochs}
                    onChange={(e) => setEpochs(Number(e.target.value))}
                    inputProps={{ min: 50, max: 200 }}
                  />
                </Box>

                <Button
                  variant="contained"
                  onClick={() => trainModel(customSymbol)}
                  disabled={!customSymbol || loading}
                  startIcon={<PlayArrowIcon />}
                  fullWidth
                >
                  Train Custom Model
                </Button>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Card>
              <CardHeader title="Training Status" />
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
        </Box>
      </TabPanel>

      {/* Price Predictions Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
          <Box>
            <Card>
              <CardHeader title="Prediction Settings" />
              <CardContent>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Select Stock</InputLabel>
                  <Select
                    value={selectedSymbol}
                    onChange={(e) => setSelectedSymbol(e.target.value)}
                    label="Select Stock"
                  >
                    {symbols.map((symbol) => (
                      <MenuItem key={symbol} value={symbol}>
                        {symbol}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  label="Custom Symbol"
                  value={customSymbol}
                  onChange={(e) => setCustomSymbol(e.target.value.toUpperCase())}
                  placeholder="Or enter custom symbol"
                  sx={{ mb: 2 }}
                />

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
                  startIcon={<TrendingUpIcon />}
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
                  <TrendingUpIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
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
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Select Stock</InputLabel>
                  <Select
                    value={selectedSymbol}
                    onChange={(e) => setSelectedSymbol(e.target.value)}
                    label="Select Stock"
                  >
                    {symbols.map((symbol) => (
                      <MenuItem key={symbol} value={symbol}>
                        {symbol}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  label="Custom Symbol"
                  value={customSymbol}
                  onChange={(e) => setCustomSymbol(e.target.value.toUpperCase())}
                  placeholder="Or enter custom symbol"
                  sx={{ mb: 2 }}
                />

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
