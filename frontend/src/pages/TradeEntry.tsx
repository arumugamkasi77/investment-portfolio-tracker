import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Paper,
    Box,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Alert,
    CircularProgress,
    Autocomplete,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    Tabs,
    Tab,
    InputAdornment,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import { tradeApi, portfolioApi, stockApi, optionApi } from '../services/api';
import { TradeFormData } from '../types';
import { Edit as EditIcon, Delete as DeleteIcon, Visibility as ViewIcon, Search as SearchIcon, FilterList as FilterIcon } from '@mui/icons-material';

const TradeEntry: React.FC = () => {
    const [portfolios, setPortfolios] = useState<any[]>([]);
    const [stocks, setStocks] = useState<any[]>([]);
    const [options, setOptions] = useState<any[]>([]);
    const [trades, setTrades] = useState<any[]>([]);
    const [submitLoading, setSubmitLoading] = useState(false);
    const [tradesLoading, setTradesLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [tabValue, setTabValue] = useState(0);
    const [editingTrade, setEditingTrade] = useState<any | null>(null);
    const [viewingTrade, setViewingTrade] = useState<any | null>(null);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [tradeToDelete, setTradeToDelete] = useState<any | null>(null);

    // Search and filter states
    const [searchTerm, setSearchTerm] = useState('');
    const [filterPortfolio, setFilterPortfolio] = useState<string>('');
    const [filterSymbol, setFilterSymbol] = useState<string>('');
    const [filterTradeType, setFilterTradeType] = useState<string>('');

    const [formData, setFormData] = useState<TradeFormData>({
        portfolio_name: '',
        symbol: '',
        instrument_type: 'STOCK',
        quantity: 0,
        trade_type: 'BUY',
        executed_price: 0,
        brokerage: 0,
        remarks: '',
        trade_date: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
    });

    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(dayjs());

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // Load regular portfolios (used in trades)
            const portfolioResponse = await portfolioApi.getPortfolios();
            setPortfolios(portfolioResponse.data || []);

            // Load stocks
            const stockResponse = await stockApi.getStocks();
            setStocks(stockResponse.data || []);

            // Load options
            const optionResponse = await optionApi.getOptions();
            setOptions(optionResponse.data || []);

            // Load trades
            await loadTrades();
        } catch (err: any) {
            console.error('Error loading data:', err);
            setError('Failed to load data');
        }
    };

    const loadTrades = async () => {
        try {
            setTradesLoading(true);
            const response = await tradeApi.getTrades();
            setTrades(response.data || []);
        } catch (err: any) {
            console.error('Error loading trades:', err);
            setError('Failed to load trades');
        } finally {
            setTradesLoading(false);
        }
    };

    const getSymbolOptions = () => {
        if (formData.instrument_type === 'STOCK') {
            return stocks.map(stock => stock.symbol);
        } else {
            return options.map(option => option.option_symbol || `${option.underlying_symbol} ${option.strike_price}${option.option_type[0]} ${option.expiration_date}`);
        }
    };

    const getSymbolHelperText = () => {
        if (formData.instrument_type === 'STOCK') {
            return 'Select a stock symbol from your database';
        } else {
            return 'Select an option contract from your database';
        }
    };

    // Filter trades based on search and filter criteria
    const filteredTrades = trades.filter(trade => {
        const matchesSearch = searchTerm === '' ||
            trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
            trade.portfolio_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            trade.remarks?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesPortfolio = filterPortfolio === '' || trade.portfolio_name === filterPortfolio;
        const matchesSymbol = filterSymbol === '' || trade.symbol === filterSymbol;
        const matchesTradeType = filterTradeType === '' || trade.trade_type === filterTradeType;

        return matchesSearch && matchesPortfolio && matchesSymbol && matchesTradeType;
    });

    const handleInputChange = (field: keyof TradeFormData, value: any) => {
        setFormData(prev => ({
            ...prev,
            [field]: value,
        }));

        // Clear symbol when instrument type changes
        if (field === 'instrument_type') {
            setFormData(prev => ({
                ...prev,
                [field]: value,
                symbol: '', // Clear symbol when switching types
            }));
        }

        // Clear messages when user starts typing
        if (error) setError(null);
        if (success) setSuccess(null);
    };

    const handleDateChange = (date: Dayjs | null) => {
        setSelectedDate(date);
        if (date) {
            handleInputChange('trade_date', date.format('YYYY-MM-DDTHH:mm:ss'));
        }
    };

    const validateForm = (): string | null => {
        if (!formData.portfolio_name.trim()) return 'Portfolio name is required';
        if (!formData.symbol.trim()) return 'Symbol is required';
        if (formData.quantity <= 0) return 'Quantity must be greater than 0';
        if (formData.executed_price <= 0) return 'Executed price must be greater than 0';
        if (formData.brokerage < 0) return 'Brokerage cannot be negative';
        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const validationError = validateForm();
        if (validationError) {
            setError(validationError);
            return;
        }

        try {
            setSubmitLoading(true);
            setError(null);
            setSuccess(null);

            const submitData = {
                ...formData,
                symbol: formData.symbol.toUpperCase(),
                trade_date: selectedDate?.format('YYYY-MM-DDTHH:mm:ss') || dayjs().format('YYYY-MM-DDTHH:mm:ss'),
            };

            const response = await tradeApi.createTrade(submitData);

            setSuccess(`Trade created successfully! Trade ID: ${response.data.trade_id}`);

            // Reload trades to show the new one
            await loadTrades();

            // Reset form
            setFormData({
                portfolio_name: formData.portfolio_name, // Keep the portfolio name for convenience
                symbol: '',
                instrument_type: 'STOCK',
                quantity: 0,
                trade_type: 'BUY',
                executed_price: 0,
                brokerage: 0,
                remarks: '',
                trade_date: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
            });
            setSelectedDate(dayjs());

        } catch (err: any) {
            console.error('Error creating trade:', err);

            // Handle validation errors from backend
            if (err.response?.data?.detail && Array.isArray(err.response.data.detail)) {
                const validationErrors = err.response.data.detail
                    .map((error: any) => `${error.loc?.join('.')}: ${error.msg}`)
                    .join(', ');
                setError(`Validation error: ${validationErrors}`);
            } else {
                setError(err.response?.data?.detail || err.message || 'Failed to create trade');
            }
        } finally {
            setSubmitLoading(false);
        }
    };

    const handleEditTrade = (trade: any) => {
        setEditingTrade(trade);
        setFormData({
            portfolio_name: trade.portfolio_name,
            symbol: trade.symbol,
            instrument_type: trade.instrument_type,
            quantity: trade.quantity,
            trade_type: trade.trade_type,
            executed_price: trade.executed_price,
            brokerage: trade.brokerage,
            remarks: trade.remarks || '',
            trade_date: trade.trade_date,
        });
        setSelectedDate(dayjs(trade.trade_date));
        setTabValue(0); // Switch to form tab
    };

    const handleUpdateTrade = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingTrade) return;

        const validationError = validateForm();
        if (validationError) {
            setError(validationError);
            return;
        }

        try {
            setSubmitLoading(true);
            setError(null);
            setSuccess(null);

            const submitData = {
                ...formData,
                symbol: formData.symbol.toUpperCase(),
                trade_date: selectedDate?.format('YYYY-MM-DDTHH:mm:ss') || dayjs().format('YYYY-MM-DDTHH:mm:ss'),
            };

            await tradeApi.updateTrade(editingTrade._id, submitData);
            setSuccess('Trade updated successfully!');

            // Reload trades and reset form
            await loadTrades();
            setEditingTrade(null);
            setFormData({
                portfolio_name: '',
                symbol: '',
                instrument_type: 'STOCK',
                quantity: 0,
                trade_type: 'BUY',
                executed_price: 0,
                brokerage: 0,
                remarks: '',
                trade_date: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
            });
            setSelectedDate(dayjs());
            setTabValue(1); // Switch back to trades list

        } catch (err: any) {
            console.error('Error updating trade:', err);
            if (err.response?.data?.detail && Array.isArray(err.response.data.detail)) {
                const validationErrors = err.response.data.detail
                    .map((error: any) => `${error.loc?.join('.')}: ${error.msg}`)
                    .join(', ');
                setError(`Validation error: ${validationErrors}`);
            } else {
                setError(err.response?.data?.detail || err.message || 'Failed to update trade');
            }
        } finally {
            setSubmitLoading(false);
        }
    };

    const handleDeleteTrade = async () => {
        if (!tradeToDelete) return;

        try {
            await tradeApi.deleteTrade(tradeToDelete._id);
            setSuccess('Trade deleted successfully!');
            await loadTrades();
        } catch (err: any) {
            console.error('Error deleting trade:', err);
            setError('Failed to delete trade');
        } finally {
            setDeleteConfirmOpen(false);
            setTradeToDelete(null);
        }
    };

    const handleCancelEdit = () => {
        setEditingTrade(null);
        setFormData({
            portfolio_name: '',
            symbol: '',
            instrument_type: 'STOCK',
            quantity: 0,
            trade_type: 'BUY',
            executed_price: 0,
            brokerage: 0,
            remarks: '',
            trade_date: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
        });
        setSelectedDate(dayjs());
        setError(null);
        setSuccess(null);
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
        }).format(amount);
    };

    const formatDate = (dateString: string) => {
        return dayjs(dateString).format('MMM DD, YYYY HH:mm');
    };

    return (
        <Container maxWidth="xl" sx={{ width: '90%', mx: 'auto' }}>
            <Paper sx={{ p: 2 }}>
                <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 1 }}>
                    Trade Management
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                    Create, view, edit, and manage your investment trades
                </Typography>

                <Tabs value={tabValue} onChange={(_, newValue) => {
                    setTabValue(newValue);
                    if (newValue === 1) {
                        // Reload trades when switching to trades list tab
                        loadTrades();
                    }
                }} sx={{ mb: 2 }}>
                    <Tab label={editingTrade ? "Edit Trade" : "Add Trade"} />
                    <Tab label={`All Trades (${trades.length})`} />
                </Tabs>

                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}

                {success && (
                    <Alert severity="success" sx={{ mb: 3 }}>
                        {success}
                    </Alert>
                )}

                {tabValue === 0 && (
                    <Box component="form" onSubmit={editingTrade ? handleUpdateTrade : handleSubmit} sx={{ mt: 1 }}>
                        <Box sx={{ display: 'grid', gap: 2 }}>
                            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                                <Autocomplete
                                    freeSolo
                                    options={portfolios.map(p => p.portfolio_name)}
                                    value={formData.portfolio_name}
                                    onInputChange={(_, value) => handleInputChange('portfolio_name', value || '')}
                                    renderInput={(params) => (
                                        <TextField
                                            {...params}
                                            label="Portfolio Name"
                                            required
                                            fullWidth
                                            helperText="Select from existing portfolios or enter a new one"
                                        />
                                    )}
                                />

                                <Autocomplete
                                    freeSolo
                                    options={getSymbolOptions()}
                                    value={formData.symbol}
                                    onInputChange={(_, value) => handleInputChange('symbol', value || '')}
                                    renderInput={(params) => (
                                        <TextField
                                            {...params}
                                            label="Symbol"
                                            required
                                            fullWidth
                                            helperText={getSymbolHelperText()}
                                            inputProps={{
                                                ...params.inputProps,
                                                style: { textTransform: 'uppercase' }
                                            }}
                                        />
                                    )}
                                />

                                <FormControl fullWidth required>
                                    <InputLabel>Instrument Type</InputLabel>
                                    <Select
                                        value={formData.instrument_type}
                                        label="Instrument Type"
                                        onChange={(e) => handleInputChange('instrument_type', e.target.value)}
                                    >
                                        <MenuItem value="STOCK">Stock</MenuItem>
                                        <MenuItem value="OPTION">Listed Option</MenuItem>
                                    </Select>
                                </FormControl>

                                <FormControl fullWidth required>
                                    <InputLabel>Trade Type</InputLabel>
                                    <Select
                                        value={formData.trade_type}
                                        label="Trade Type"
                                        onChange={(e) => handleInputChange('trade_type', e.target.value)}
                                    >
                                        <MenuItem value="BUY">Buy</MenuItem>
                                        <MenuItem value="SELL">Sell</MenuItem>
                                    </Select>
                                </FormControl>
                            </Box>

                            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                                <TextField
                                    label="Quantity"
                                    type="number"
                                    value={formData.quantity || ''}
                                    onChange={(e) => handleInputChange('quantity', parseInt(e.target.value) || 0)}
                                    required
                                    fullWidth
                                    inputProps={{ min: 1 }}
                                    helperText="Number of shares/contracts"
                                />

                                <TextField
                                    label="Executed Price"
                                    type="number"
                                    value={formData.executed_price || ''}
                                    onChange={(e) => handleInputChange('executed_price', parseFloat(e.target.value) || 0)}
                                    required
                                    fullWidth
                                    inputProps={{ min: 0, step: 0.01 }}
                                    helperText="Price per share/contract"
                                />

                                <TextField
                                    label="Brokerage"
                                    type="number"
                                    value={formData.brokerage || ''}
                                    onChange={(e) => handleInputChange('brokerage', parseFloat(e.target.value) || 0)}
                                    fullWidth
                                    inputProps={{ min: 0, step: 0.01 }}
                                    helperText="Commission/fees"
                                />
                            </Box>

                            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                                <LocalizationProvider dateAdapter={AdapterDayjs}>
                                    <DatePicker
                                        label="Trade Date"
                                        value={selectedDate}
                                        onChange={handleDateChange}
                                        slotProps={{
                                            textField: {
                                                fullWidth: true,
                                                required: true,
                                            },
                                        }}
                                    />
                                </LocalizationProvider>
                            </Box>

                            <TextField
                                label="Remarks"
                                value={formData.remarks}
                                onChange={(e) => handleInputChange('remarks', e.target.value)}
                                fullWidth
                                multiline
                                rows={2}
                                helperText="Optional notes about this trade"
                            />

                            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                                {editingTrade && (
                                    <Button
                                        type="button"
                                        variant="outlined"
                                        onClick={handleCancelEdit}
                                    >
                                        Cancel
                                    </Button>
                                )}
                                <Button
                                    type="button"
                                    variant="outlined"
                                    onClick={() => {
                                        setFormData({
                                            portfolio_name: '',
                                            symbol: '',
                                            instrument_type: 'STOCK',
                                            quantity: 0,
                                            trade_type: 'BUY',
                                            executed_price: 0,
                                            brokerage: 0,
                                            remarks: '',
                                            trade_date: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
                                        });
                                        setSelectedDate(dayjs());
                                        setError(null);
                                        setSuccess(null);
                                    }}
                                >
                                    Clear
                                </Button>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    disabled={submitLoading}
                                    sx={{ minWidth: 120 }}
                                >
                                    {submitLoading ? <CircularProgress size={24} /> : (editingTrade ? 'Update Trade' : 'Create Trade')}
                                </Button>
                            </Box>
                        </Box>
                    </Box>
                )}

                {tabValue === 1 && (
                    <Box>
                        {/* Search and Filter Controls */}
                        <Paper sx={{ p: 1.5, mb: 1.5 }}>
                            <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' } }}>
                                {/* Global Search */}
                                <TextField
                                    label="Search All Fields"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    size="small"
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <SearchIcon />
                                            </InputAdornment>
                                        ),
                                    }}
                                />

                                {/* Portfolio Filter */}
                                <FormControl size="small">
                                    <InputLabel>Portfolio</InputLabel>
                                    <Select
                                        value={filterPortfolio}
                                        onChange={(e) => setFilterPortfolio(e.target.value)}
                                        label="Portfolio"
                                    >
                                        <MenuItem value="">All Portfolios</MenuItem>
                                        {portfolios.map((portfolio) => (
                                            <MenuItem key={portfolio._id} value={portfolio.portfolio_name}>
                                                {portfolio.portfolio_name}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>

                                {/* Symbol Filter */}
                                <FormControl size="small">
                                    <InputLabel>Symbol</InputLabel>
                                    <Select
                                        value={filterSymbol}
                                        onChange={(e) => setFilterSymbol(e.target.value)}
                                        label="Symbol"
                                    >
                                        <MenuItem value="">All Symbols</MenuItem>
                                        {stocks.map((stock) => (
                                            <MenuItem key={stock._id} value={stock.symbol}>
                                                {stock.symbol}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>

                                {/* Trade Type Filter */}
                                <FormControl size="small">
                                    <InputLabel>Trade Type</InputLabel>
                                    <Select
                                        value={filterTradeType}
                                        onChange={(e) => setFilterTradeType(e.target.value)}
                                        label="Trade Type"
                                    >
                                        <MenuItem value="">All Types</MenuItem>
                                        <MenuItem value="BUY">BUY</MenuItem>
                                        <MenuItem value="SELL">SELL</MenuItem>
                                    </Select>
                                </FormControl>
                            </Box>

                            {/* Results Count */}
                            <Box sx={{ mt: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" color="text.secondary">
                                    Showing {filteredTrades.length} of {trades.length} trades
                                </Typography>
                                <Button
                                    size="small"
                                    onClick={() => {
                                        setSearchTerm('');
                                        setFilterPortfolio('');
                                        setFilterSymbol('');
                                        setFilterTradeType('');
                                    }}
                                    startIcon={<FilterIcon />}
                                >
                                    Clear Filters
                                </Button>
                            </Box>
                        </Paper>

                        {tradesLoading ? (
                            <Box display="flex" justifyContent="center" p={2}>
                                <CircularProgress />
                            </Box>
                        ) : (
                            <TableContainer>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Date</TableCell>
                                            <TableCell>Portfolio</TableCell>
                                            <TableCell>Symbol</TableCell>
                                            <TableCell>Trade Type</TableCell>
                                            <TableCell align="right">Quantity</TableCell>
                                            <TableCell align="right">Price</TableCell>
                                            <TableCell align="right">Total</TableCell>
                                            <TableCell align="right">Brokerage</TableCell>
                                            <TableCell>Remarks</TableCell>
                                            <TableCell align="center">Actions</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {filteredTrades.map((trade) => (
                                            <TableRow key={trade._id} hover>
                                                <TableCell>{formatDate(trade.trade_date)}</TableCell>
                                                <TableCell>{trade.portfolio_name}</TableCell>
                                                <TableCell>
                                                    <Box display="flex" alignItems="center" gap={1}>
                                                        {trade.symbol}
                                                        <Chip
                                                            label={trade.instrument_type}
                                                            size="small"
                                                            variant="outlined"
                                                            color={trade.instrument_type === 'STOCK' ? 'primary' : 'secondary'}
                                                        />
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={trade.trade_type}
                                                        size="small"
                                                        color={trade.trade_type === 'BUY' ? 'success' : 'error'}
                                                    />
                                                </TableCell>
                                                <TableCell align="right">{trade.quantity}</TableCell>
                                                <TableCell align="right">{formatCurrency(trade.executed_price)}</TableCell>
                                                <TableCell align="right">
                                                    {formatCurrency(trade.quantity * trade.executed_price)}
                                                </TableCell>
                                                <TableCell align="right">{formatCurrency(trade.brokerage)}</TableCell>
                                                <TableCell>{trade.remarks || '-'}</TableCell>
                                                <TableCell align="center">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => setViewingTrade(trade)}
                                                        title="View Details"
                                                    >
                                                        <ViewIcon />
                                                    </IconButton>
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleEditTrade(trade)}
                                                        title="Edit Trade"
                                                    >
                                                        <EditIcon />
                                                    </IconButton>
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => {
                                                            setTradeToDelete(trade);
                                                            setDeleteConfirmOpen(true);
                                                        }}
                                                        title="Delete Trade"
                                                        color="error"
                                                    >
                                                        <DeleteIcon />
                                                    </IconButton>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                        {filteredTrades.length === 0 && (
                                            <TableRow>
                                                <TableCell colSpan={11} align="center" sx={{ py: 2 }}>
                                                    <Typography color="text.secondary">
                                                        {trades.length === 0
                                                            ? 'No trades found. Create your first trade using the form above.'
                                                            : 'No trades match your current filters. Try adjusting your search criteria.'
                                                        }
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        )}
                    </Box>
                )}

                {/* View Trade Dialog */}
                <Dialog open={!!viewingTrade} onClose={() => setViewingTrade(null)} maxWidth="sm" fullWidth>
                    <DialogTitle>Trade Details</DialogTitle>
                    <DialogContent>
                        {viewingTrade && (
                            <Box sx={{ display: 'grid', gap: 2, pt: 1 }}>
                                <TextField label="Trade ID" value={viewingTrade._id} InputProps={{ readOnly: true }} />
                                <TextField label="Portfolio" value={viewingTrade.portfolio_name} InputProps={{ readOnly: true }} />
                                <TextField label="Symbol" value={viewingTrade.symbol} InputProps={{ readOnly: true }} />
                                <TextField label="Instrument Type" value={viewingTrade.instrument_type} InputProps={{ readOnly: true }} />
                                <TextField label="Trade Type" value={viewingTrade.trade_type} InputProps={{ readOnly: true }} />
                                <TextField label="Quantity" value={viewingTrade.quantity} InputProps={{ readOnly: true }} />
                                <TextField label="Executed Price" value={formatCurrency(viewingTrade.executed_price)} InputProps={{ readOnly: true }} />
                                <TextField label="Total Value" value={formatCurrency(viewingTrade.quantity * viewingTrade.executed_price)} InputProps={{ readOnly: true }} />
                                <TextField label="Brokerage" value={formatCurrency(viewingTrade.brokerage)} InputProps={{ readOnly: true }} />
                                <TextField label="Trade Date" value={formatDate(viewingTrade.trade_date)} InputProps={{ readOnly: true }} />
                                {viewingTrade.remarks && (
                                    <TextField
                                        label="Remarks"
                                        value={viewingTrade.remarks}
                                        InputProps={{ readOnly: true }}
                                        multiline
                                        rows={3}
                                    />
                                )}
                            </Box>
                        )}
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setViewingTrade(null)}>Close</Button>
                    </DialogActions>
                </Dialog>

                {/* Delete Confirmation Dialog */}
                <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
                    <DialogTitle>Confirm Delete</DialogTitle>
                    <DialogContent>
                        <Typography>
                            Are you sure you want to delete this trade? This action cannot be undone.
                        </Typography>
                        {tradeToDelete && (
                            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                                <Typography variant="body2">
                                    <strong>{tradeToDelete.symbol}</strong> - {tradeToDelete.trade_type} {tradeToDelete.quantity} shares @ {formatCurrency(tradeToDelete.executed_price)}
                                </Typography>
                            </Box>
                        )}
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
                        <Button onClick={handleDeleteTrade} color="error" variant="contained">
                            Delete
                        </Button>
                    </DialogActions>
                </Dialog>
            </Paper>
        </Container>
    );
};

export default TradeEntry;
