import React, { useState, useEffect } from 'react';
import { stockApi } from '../services/api';
import {
    Container,
    Typography,
    Paper,
    Box,
    TextField,
    Button,
    Alert,
    CircularProgress,
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
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    InputAdornment,
} from '@mui/material';
import {
    Add as AddIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Search as SearchIcon,
    FilterList as FilterIcon,
} from '@mui/icons-material';

interface Stock {
    _id?: string;
    symbol: string;
    company_name: string;
    industry: string;
    sector: string;
    exchange: string;
    country: string;
    currency: string;
    market_cap?: number;
    description?: string;
    website?: string;
    created_at?: string;
    updated_at?: string;
}

const StockManagement: React.FC = () => {
    const [stocks, setStocks] = useState<Stock[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitLoading, setSubmitLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [editingStock, setEditingStock] = useState<Stock | null>(null);

    const [formData, setFormData] = useState<Stock>({
        symbol: '',
        company_name: '',
        industry: '',
        sector: '',
        exchange: '',
        country: 'US',
        currency: 'USD',
        market_cap: undefined,
        description: '',
        website: '',
    });

    // Search and filter states
    const [searchTerm, setSearchTerm] = useState('');
    const [filterExchange, setFilterExchange] = useState<string>('');
    const [filterIndustry, setFilterIndustry] = useState<string>('');

    const exchanges = ['NASDAQ', 'NYSE', 'AMEX', 'OTC', 'LSE', 'TSE', 'Other'];
    const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY'];
    const countries = ['US', 'UK', 'CA', 'JP', 'DE', 'FR', 'AU', 'CN', 'Other'];

    useEffect(() => {
        loadStocks();
    }, []);

    const loadStocks = async () => {
        try {
            setLoading(true);
            const response = await stockApi.getStocks();
            setStocks(response.data || []);
        } catch (err: any) {
            console.error('Error loading stocks:', err);
            setError('Failed to load stocks');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitLoading(true);
        setError(null);
        setSuccess(null);

        try {
            if (editingStock) {
                // TODO: Update existing stock
                // await stockApi.updateStock(editingStock._id!, formData);
                setSuccess('Stock updated successfully!');
            } else {
                // TODO: Create new stock
                // await stockApi.createStock(formData);
                setSuccess('Stock created successfully!');
            }

            handleCloseDialog();
            loadStocks();
        } catch (err: any) {
            console.error('Error saving stock:', err);
            setError(err.response?.data?.detail || 'Failed to save stock');
        } finally {
            setSubmitLoading(false);
        }
    };

    const handleEdit = (stock: Stock) => {
        setEditingStock(stock);
        setFormData({ ...stock });
        setOpenDialog(true);
    };

    const handleDelete = async (stockId: string) => {
        if (!window.confirm('Are you sure you want to delete this stock?')) {
            return;
        }

        try {
            // TODO: Delete stock
            // await stockApi.deleteStock(stockId);
            setSuccess('Stock deleted successfully!');
            loadStocks();
        } catch (err: any) {
            console.error('Error deleting stock:', err);
            setError('Failed to delete stock');
        }
    };

    const handleOpenDialog = () => {
        setEditingStock(null);
        setFormData({
            symbol: '',
            company_name: '',
            industry: '',
            sector: '',
            exchange: '',
            country: 'US',
            currency: 'USD',
            market_cap: undefined,
            description: '',
            website: '',
        });
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingStock(null);
        setError(null);
    };

    const handleInputChange = (field: keyof Stock, value: any) => {
        setFormData(prev => ({
            ...prev,
            [field]: value,
        }));
    };

    // Filter stocks based on search and filter criteria
    const filteredStocks = stocks.filter(stock => {
        const matchesSearch = searchTerm === '' ||
            stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
            stock.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            stock.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
            stock.sector.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesExchange = filterExchange === '' || stock.exchange === filterExchange;
        const matchesIndustry = filterIndustry === '' || stock.industry === filterIndustry;

        return matchesSearch && matchesExchange && matchesIndustry;
    });

    const formatMarketCap = (marketCap?: number) => {
        if (!marketCap) return '-';
        if (marketCap >= 1e12) return `$${(marketCap / 1e12).toFixed(2)}T`;
        if (marketCap >= 1e9) return `$${(marketCap / 1e9).toFixed(2)}B`;
        if (marketCap >= 1e6) return `$${(marketCap / 1e6).toFixed(2)}M`;
        return `$${marketCap.toLocaleString()}`;
    };

    return (
        <Container maxWidth="xl" sx={{ width: '90%', mx: 'auto', py: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h4" component="h1">
                    Stock Management
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleOpenDialog}
                >
                    Add Stock
                </Button>
            </Box>

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

            {/* Search and Filter Controls */}
            <Paper sx={{ p: 1.5, mb: 1.5 }}>
                <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' } }}>
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

                    {/* Exchange Filter */}
                    <FormControl size="small">
                        <InputLabel>Exchange</InputLabel>
                        <Select
                            value={filterExchange}
                            onChange={(e) => setFilterExchange(e.target.value)}
                            label="Exchange"
                        >
                            <MenuItem value="">All Exchanges</MenuItem>
                            {exchanges.map((exchange) => (
                                <MenuItem key={exchange} value={exchange}>
                                    {exchange}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {/* Industry Filter */}
                    <FormControl size="small">
                        <InputLabel>Industry</InputLabel>
                        <Select
                            value={filterIndustry}
                            onChange={(e) => setFilterIndustry(e.target.value)}
                            label="Industry"
                        >
                            <MenuItem value="">All Industries</MenuItem>
                            {Array.from(new Set(stocks.map(s => s.industry))).map((industry) => (
                                <MenuItem key={industry} value={industry}>
                                    {industry}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Box>

                {/* Results Count */}
                <Box sx={{ mt: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                        Showing {filteredStocks.length} of {stocks.length} stocks
                    </Typography>
                    <Button
                        size="small"
                        onClick={() => {
                            setSearchTerm('');
                            setFilterExchange('');
                            setFilterIndustry('');
                        }}
                        startIcon={<FilterIcon />}
                    >
                        Clear Filters
                    </Button>
                </Box>
            </Paper>

            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                    <CircularProgress />
                </Box>
            ) : (
                <Paper sx={{ p: 1 }}>
                    <TableContainer>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Symbol</TableCell>
                                    <TableCell>Company Name</TableCell>
                                    <TableCell>Industry</TableCell>
                                    <TableCell>Sector</TableCell>
                                    <TableCell>Exchange</TableCell>
                                    <TableCell>Market Cap</TableCell>
                                    <TableCell>Currency</TableCell>
                                    <TableCell align="center">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {filteredStocks.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={8} align="center">
                                            <Typography variant="body1" color="text.secondary">
                                                {stocks.length === 0
                                                    ? 'No stocks found. Add your first stock!'
                                                    : 'No stocks match your current filters. Try adjusting your search criteria.'
                                                }
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredStocks.map((stock) => (
                                        <TableRow key={stock._id}>
                                            <TableCell>
                                                <Typography variant="subtitle2" fontWeight="bold">
                                                    {stock.symbol}
                                                </Typography>
                                            </TableCell>
                                            <TableCell>{stock.company_name}</TableCell>
                                            <TableCell>{stock.industry}</TableCell>
                                            <TableCell>{stock.sector}</TableCell>
                                            <TableCell>{stock.exchange}</TableCell>
                                            <TableCell>{formatMarketCap(stock.market_cap)}</TableCell>
                                            <TableCell>{stock.currency}</TableCell>
                                            <TableCell align="center">
                                                <IconButton
                                                    color="primary"
                                                    onClick={() => handleEdit(stock)}
                                                    size="small"
                                                >
                                                    <EditIcon />
                                                </IconButton>
                                                <IconButton
                                                    color="error"
                                                    onClick={() => handleDelete(stock._id!)}
                                                    size="small"
                                                >
                                                    <DeleteIcon />
                                                </IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Paper>
            )}

            {/* Add/Edit Stock Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                <DialogTitle>
                    {editingStock ? 'Edit Stock' : 'Add New Stock'}
                </DialogTitle>
                <DialogContent>
                    <Box component="form" onSubmit={handleSubmit} sx={{ pt: 2 }}>
                        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
                            <TextField
                                label="Stock Symbol"
                                value={formData.symbol}
                                onChange={(e) => handleInputChange('symbol', e.target.value.toUpperCase())}
                                required
                                fullWidth
                                helperText="e.g., AAPL, NVDA, TSLA"
                                inputProps={{ style: { textTransform: 'uppercase' } }}
                            />

                            <TextField
                                label="Company Name"
                                value={formData.company_name}
                                onChange={(e) => handleInputChange('company_name', e.target.value)}
                                required
                                fullWidth
                                helperText="Full company name"
                            />

                            <TextField
                                label="Industry"
                                value={formData.industry}
                                onChange={(e) => handleInputChange('industry', e.target.value)}
                                required
                                fullWidth
                                helperText="e.g., Technology, Healthcare"
                            />

                            <TextField
                                label="Sector"
                                value={formData.sector}
                                onChange={(e) => handleInputChange('sector', e.target.value)}
                                required
                                fullWidth
                                helperText="e.g., Consumer Electronics, Biotechnology"
                            />

                            <FormControl fullWidth required>
                                <InputLabel>Exchange</InputLabel>
                                <Select
                                    value={formData.exchange}
                                    label="Exchange"
                                    onChange={(e) => handleInputChange('exchange', e.target.value)}
                                >
                                    {exchanges.map((exchange) => (
                                        <MenuItem key={exchange} value={exchange}>
                                            {exchange}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>

                            <FormControl fullWidth required>
                                <InputLabel>Country</InputLabel>
                                <Select
                                    value={formData.country}
                                    label="Country"
                                    onChange={(e) => handleInputChange('country', e.target.value)}
                                >
                                    {countries.map((country) => (
                                        <MenuItem key={country} value={country}>
                                            {country}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>

                            <FormControl fullWidth required>
                                <InputLabel>Currency</InputLabel>
                                <Select
                                    value={formData.currency}
                                    label="Currency"
                                    onChange={(e) => handleInputChange('currency', e.target.value)}
                                >
                                    {currencies.map((currency) => (
                                        <MenuItem key={currency} value={currency}>
                                            {currency}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>

                            <TextField
                                label="Market Cap"
                                type="number"
                                value={formData.market_cap || ''}
                                onChange={(e) => handleInputChange('market_cap', parseFloat(e.target.value) || undefined)}
                                fullWidth
                                helperText="Market capitalization in dollars"
                                inputProps={{ min: 0 }}
                            />

                            <TextField
                                label="Website"
                                value={formData.website}
                                onChange={(e) => handleInputChange('website', e.target.value)}
                                fullWidth
                                helperText="Company website URL"
                                sx={{ gridColumn: { md: 'span 2' } }}
                            />

                            <TextField
                                label="Description"
                                value={formData.description}
                                onChange={(e) => handleInputChange('description', e.target.value)}
                                fullWidth
                                multiline
                                rows={3}
                                helperText="Brief description of the company"
                                sx={{ gridColumn: { md: 'span 2' } }}
                            />
                        </Box>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>Cancel</Button>
                    <Button
                        onClick={handleSubmit}
                        variant="contained"
                        disabled={submitLoading || !formData.symbol || !formData.company_name}
                    >
                        {submitLoading ? (
                            <CircularProgress size={24} />
                        ) : (
                            editingStock ? 'Update' : 'Create'
                        )}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default StockManagement;
