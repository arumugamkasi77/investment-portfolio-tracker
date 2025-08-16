import React, { useState, useEffect } from 'react';
import { optionApi } from '../services/api';
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
    Chip,
    InputAdornment,
} from '@mui/material';
import {
    Add as AddIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Search as SearchIcon,
    FilterList as FilterIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';

interface StockOption {
    _id?: string;
    underlying_symbol: string;
    option_symbol: string;
    option_type: 'CALL' | 'PUT';
    strike_price: number;
    expiration_date: string;
    contract_size: number;
    exchange: string;
    currency: string;
    description?: string;
    created_at?: string;
    updated_at?: string;
}

const OptionManagement: React.FC = () => {
    const [options, setOptions] = useState<StockOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitLoading, setSubmitLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [editingOption, setEditingOption] = useState<StockOption | null>(null);
    const [selectedExpirationDate, setSelectedExpirationDate] = useState<Dayjs | null>(null);

    const [formData, setFormData] = useState<StockOption>({
        underlying_symbol: '',
        option_symbol: '',
        option_type: 'CALL',
        strike_price: 0,
        expiration_date: '',
        contract_size: 100,
        exchange: 'CBOE',
        currency: 'USD',
        description: '',
    });

    // Search and filter states
    const [searchTerm, setSearchTerm] = useState('');
    const [filterUnderlying, setFilterUnderlying] = useState<string>('');
    const [filterOptionType, setFilterOptionType] = useState<string>('');
    const [filterExchange, setFilterExchange] = useState<string>('');

    const exchanges = ['CBOE', 'ISE', 'PHLX', 'AMEX', 'NYSE Arca', 'NASDAQ Options', 'Other'];
    const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD'];
    const optionTypes = ['CALL', 'PUT'];

    useEffect(() => {
        loadOptions();
    }, []);

    const loadOptions = async () => {
        try {
            setLoading(true);
            const response = await optionApi.getOptions();
            setOptions(response.data || []);
        } catch (err: any) {
            console.error('Error loading options:', err);
            setError('Failed to load options');
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
            // Validate required fields
            if (!formData.underlying_symbol || formData.strike_price <= 0 || !selectedExpirationDate ||
                formData.contract_size <= 0 || !formData.exchange || !formData.currency) {
                setError('Please fill in all required fields correctly');
                return;
            }

            // Validate underlying symbol is not an option symbol
            if (formData.underlying_symbol.length > 10 || /\d/.test(formData.underlying_symbol)) {
                setError('Underlying Symbol should be a stock symbol only (e.g., AAPL, NVDA). Do not enter option symbols here.');
                return;
            }

            // Prepare the data to send
            const optionData = {
                underlying_symbol: formData.underlying_symbol.toUpperCase(),
                option_symbol: formData.option_symbol || undefined, // Only send if provided
                option_type: formData.option_type,
                strike_price: formData.strike_price,
                expiration_date: selectedExpirationDate.format('YYYY-MM-DD'),
                contract_size: formData.contract_size,
                exchange: formData.exchange,
                currency: formData.currency.toUpperCase(),
                description: formData.description || undefined, // Only send if provided
            };

            console.log('Sending option data:', optionData);
            console.log('Form data:', formData);
            console.log('Selected expiration date:', selectedExpirationDate);

            if (editingOption) {
                // Update existing option
                await optionApi.updateOption(editingOption._id!, optionData);
                setSuccess('Option updated successfully!');
            } else {
                // Create new option
                await optionApi.createOption(optionData);
                setSuccess('Option created successfully!');
            }

            handleCloseDialog();
            loadOptions();
        } catch (err: any) {
            console.error('Error saving option:', err);
            console.error('Error response data:', err.response?.data);
            console.error('Error response status:', err.response?.status);
            console.error('Error response headers:', err.response?.headers);

            // Show detailed error message
            let errorMessage = 'Failed to save option';
            if (err.response?.data?.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    errorMessage += ': ' + err.response.data.detail.map((d: any) => d.msg).join(', ');
                } else {
                    errorMessage += ': ' + err.response.data.detail;
                }
            } else if (err.message) {
                errorMessage += ': ' + err.message;
            }

            setError(errorMessage);
        } finally {
            setSubmitLoading(false);
        }
    };

    const handleEdit = (option: StockOption) => {
        setEditingOption(option);
        setFormData({ ...option });
        setSelectedExpirationDate(option.expiration_date ? dayjs(option.expiration_date) : null);
        setOpenDialog(true);
    };

    const handleDelete = async (optionId: string) => {
        if (!window.confirm('Are you sure you want to delete this option?')) {
            return;
        }

        try {
            await optionApi.deleteOption(optionId);
            setSuccess('Option deleted successfully!');
            loadOptions();
        } catch (err: any) {
            console.error('Error deleting option:', err);
            setError('Failed to delete option: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleOpenDialog = () => {
        setEditingOption(null);
        setFormData({
            underlying_symbol: '',
            option_symbol: '',
            option_type: 'CALL',
            strike_price: 0,
            expiration_date: '',
            contract_size: 100,
            exchange: 'CBOE',
            currency: 'USD',
            description: '',
        });
        setSelectedExpirationDate(null);
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingOption(null);
        setSelectedExpirationDate(null);
        setError(null);
    };

    const handleInputChange = (field: keyof StockOption, value: any) => {
        setFormData(prev => ({
            ...prev,
            [field]: value,
        }));
    };

    // Filter options based on search and filter criteria
    const filteredOptions = options.filter(option => {
        const matchesSearch = searchTerm === '' ||
            option.underlying_symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
            option.option_symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
            option.description?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesUnderlying = filterUnderlying === '' || option.underlying_symbol === filterUnderlying;
        const matchesOptionType = filterOptionType === '' || option.option_type === filterOptionType;
        const matchesExchange = filterExchange === '' || option.exchange === filterExchange;

        return matchesSearch && matchesUnderlying && matchesOptionType && matchesExchange;
    });

    const handleDateChange = (date: Dayjs | null) => {
        setSelectedExpirationDate(date);
    };

    const formatOptionSymbol = (option: StockOption) => {
        const expDate = dayjs(option.expiration_date).format('YYMMDD');
        const typeCode = option.option_type === 'CALL' ? 'C' : 'P';
        const strike = (option.strike_price * 1000).toString().padStart(8, '0');
        return `${option.underlying_symbol}${expDate}${typeCode}${strike}`;
    };

    const isExpired = (expirationDate: string) => {
        return dayjs(expirationDate).isBefore(dayjs(), 'day');
    };

    return (
        <Container maxWidth="xl" sx={{ width: '90%', mx: 'auto', py: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h4" component="h1">
                    Listed Stock Options Management
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleOpenDialog}
                >
                    Add Option
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

                    {/* Underlying Symbol Filter */}
                    <FormControl size="small">
                        <InputLabel>Underlying</InputLabel>
                        <Select
                            value={filterUnderlying}
                            onChange={(e) => setFilterUnderlying(e.target.value)}
                            label="Underlying"
                        >
                            <MenuItem value="">All Underlying</MenuItem>
                            {Array.from(new Set(options.map(o => o.underlying_symbol))).map((symbol) => (
                                <MenuItem key={symbol} value={symbol}>
                                    {symbol}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {/* Option Type Filter */}
                    <FormControl size="small">
                        <InputLabel>Option Type</InputLabel>
                        <Select
                            value={filterOptionType}
                            onChange={(e) => setFilterOptionType(e.target.value)}
                            label="Option Type"
                        >
                            <MenuItem value="">All Types</MenuItem>
                            {optionTypes.map((type) => (
                                <MenuItem key={type} value={type}>
                                    {type}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

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
                </Box>

                {/* Results Count */}
                <Box sx={{ mt: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                        Showing {filteredOptions.length} of {options.length} options
                    </Typography>
                    <Button
                        size="small"
                        onClick={() => {
                            setSearchTerm('');
                            setFilterUnderlying('');
                            setFilterOptionType('');
                            setFilterExchange('');
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
                                    <TableCell>Underlying</TableCell>
                                    <TableCell>Option Symbol</TableCell>
                                    <TableCell>Type</TableCell>
                                    <TableCell>Strike Price</TableCell>
                                    <TableCell>Expiration</TableCell>
                                    <TableCell>Contract Size</TableCell>
                                    <TableCell>Exchange</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell align="center">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {filteredOptions.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={9} align="center">
                                            <Typography variant="body1" color="text.secondary">
                                                {options.length === 0
                                                    ? 'No options found. Add your first option!'
                                                    : 'No options match your current filters. Try adjusting your search criteria.'
                                                }
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredOptions.map((option) => (
                                        <TableRow key={option._id}>
                                            <TableCell>
                                                <Typography variant="subtitle2" fontWeight="bold">
                                                    {option.underlying_symbol}
                                                </Typography>
                                            </TableCell>
                                            <TableCell>
                                                <Typography variant="body2" fontFamily="monospace">
                                                    {option.option_symbol || formatOptionSymbol(option)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={option.option_type}
                                                    color={option.option_type === 'CALL' ? 'success' : 'error'}
                                                    size="small"
                                                />
                                            </TableCell>
                                            <TableCell>${option.strike_price.toFixed(2)}</TableCell>
                                            <TableCell>{dayjs(option.expiration_date).format('MMM DD, YYYY')}</TableCell>
                                            <TableCell>{option.contract_size}</TableCell>
                                            <TableCell>{option.exchange}</TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={isExpired(option.expiration_date) ? 'Expired' : 'Active'}
                                                    color={isExpired(option.expiration_date) ? 'default' : 'primary'}
                                                    size="small"
                                                />
                                            </TableCell>
                                            <TableCell align="center">
                                                <IconButton
                                                    color="primary"
                                                    onClick={() => handleEdit(option)}
                                                    size="small"
                                                >
                                                    <EditIcon />
                                                </IconButton>
                                                <IconButton
                                                    color="error"
                                                    onClick={() => handleDelete(option._id!)}
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

            {/* Add/Edit Option Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                <DialogTitle>
                    {editingOption ? 'Edit Listed Option' : 'Add New Listed Option'}
                </DialogTitle>
                <DialogContent>
                    <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                            <strong>Important:</strong> Enter the STOCK symbol (e.g., AAPL) in "Stock Symbol" field, not the full option symbol.
                            The option symbol will be auto-generated or you can enter it manually in the "Option Symbol" field.
                        </Typography>
                    </Alert>
                    <Box component="form" onSubmit={handleSubmit} sx={{ pt: 2 }}>
                        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
                            <TextField
                                label="Stock Symbol (Underlying)"
                                value={formData.underlying_symbol}
                                onChange={(e) => handleInputChange('underlying_symbol', e.target.value.toUpperCase())}
                                required
                                fullWidth
                                helperText="Enter the STOCK symbol only (e.g., AAPL, NVDA, TSLA)"
                                inputProps={{ style: { textTransform: 'uppercase' } }}
                                error={formData.underlying_symbol.length > 10}
                            />

                            <TextField
                                label="Option Symbol (Optional)"
                                value={formData.option_symbol}
                                onChange={(e) => handleInputChange('option_symbol', e.target.value.toUpperCase())}
                                fullWidth
                                helperText="Full option symbol (e.g., AAPL251219C00110000) - leave empty to auto-generate"
                                inputProps={{ style: { textTransform: 'uppercase' } }}
                            />

                            <FormControl fullWidth required>
                                <InputLabel>Option Type</InputLabel>
                                <Select
                                    value={formData.option_type}
                                    label="Option Type"
                                    onChange={(e) => handleInputChange('option_type', e.target.value)}
                                >
                                    {optionTypes.map((type) => (
                                        <MenuItem key={type} value={type}>
                                            {type}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>

                            <TextField
                                label="Strike Price"
                                type="number"
                                value={formData.strike_price || ''}
                                onChange={(e) => handleInputChange('strike_price', parseFloat(e.target.value) || 0)}
                                required
                                fullWidth
                                helperText="Strike price in dollars (must be > 0)"
                                inputProps={{ min: 0.01, step: 0.01 }}
                                error={formData.strike_price <= 0}
                            />

                            <LocalizationProvider dateAdapter={AdapterDayjs}>
                                <DatePicker
                                    label="Expiration Date"
                                    value={selectedExpirationDate}
                                    onChange={handleDateChange}
                                    slotProps={{
                                        textField: {
                                            fullWidth: true,
                                            required: true,
                                            helperText: 'Option expiration date',
                                        },
                                    }}
                                />
                            </LocalizationProvider>

                            <TextField
                                label="Contract Size"
                                type="number"
                                value={formData.contract_size || ''}
                                onChange={(e) => handleInputChange('contract_size', parseInt(e.target.value) || 100)}
                                required
                                fullWidth
                                helperText="Number of shares per contract (usually 100)"
                                inputProps={{ min: 1 }}
                                error={formData.contract_size <= 0}
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
                                label="Description"
                                value={formData.description}
                                onChange={(e) => handleInputChange('description', e.target.value)}
                                fullWidth
                                multiline
                                rows={3}
                                helperText="Optional description or notes"
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
                        disabled={
                            submitLoading ||
                            !formData.underlying_symbol ||
                            formData.strike_price <= 0 ||
                            !selectedExpirationDate ||
                            formData.contract_size <= 0 ||
                            !formData.exchange ||
                            !formData.currency
                        }
                    >
                        {submitLoading ? (
                            <CircularProgress size={24} />
                        ) : (
                            editingOption ? 'Update' : 'Create'
                        )}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default OptionManagement;
