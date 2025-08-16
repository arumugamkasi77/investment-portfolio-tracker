import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Card,
    CardContent,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Alert,
    CircularProgress,
    IconButton,
    Tooltip
} from '@mui/material';
import { TrendingUp as TrendingUpIcon, TrendingDown as TrendingDownIcon } from '@mui/icons-material';
import { Edit as EditIcon } from '@mui/icons-material';
import { portfolioApi } from '../services/api';
import { Portfolio, PortfolioPosition } from '../types';

const PortfolioView: React.FC = () => {
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
    const [positions, setPositions] = useState<PortfolioPosition[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [priceDialog, setPriceDialog] = useState({
        open: false,
        symbol: '',
        currentPrice: 0,
    });
    const [newPrice, setNewPrice] = useState<string>('');

    useEffect(() => {
        loadPortfolios();
    }, []);

    useEffect(() => {
        if (selectedPortfolio) {
            loadPortfolioPositions();
        }
    }, [selectedPortfolio]);

    const loadPortfolios = async () => {
        try {
            const response = await portfolioApi.getPortfolios();
            setPortfolios(response.data);

            // If no portfolio is selected and we have portfolios, select the first one
            if (!selectedPortfolio && response.data.length > 0) {
                setSelectedPortfolio(response.data[0].portfolio_name);
            }
        } catch (err: any) {
            console.error('Error loading portfolios:', err);
            setError('Failed to load portfolios');
        }
    };

    const loadPortfolioPositions = async () => {
        if (!selectedPortfolio) return;

        try {
            setLoading(true);
            setError(null);
            const response = await portfolioApi.getPortfolioPositions(selectedPortfolio);
            setPositions(response.data);
        } catch (err: any) {
            console.error('Error loading portfolio positions:', err);
            setError(err.response?.data?.detail || err.message || 'Failed to load portfolio positions');
        } finally {
            setLoading(false);
        }
    };

    const handleUpdatePrice = async () => {
        try {
            const price = parseFloat(newPrice);
            if (isNaN(price) || price <= 0) {
                alert('Please enter a valid price');
                return;
            }

            await portfolioApi.updateMarketPrice(selectedPortfolio, priceDialog.symbol, price);
            setPriceDialog({ open: false, symbol: '', currentPrice: 0 });
            setNewPrice('');

            // Reload positions to reflect the new price
            await loadPortfolioPositions();
        } catch (err: any) {
            console.error('Error updating price:', err);
            alert('Failed to update price: ' + (err.response?.data?.detail || err.message));
        }
    };

    const formatCurrency = (value: number): string => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(value);
    };

    const formatPercent = (value: number): string => {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    const getPLColor = (value: number): 'success' | 'error' | 'default' => {
        return value > 0 ? 'success' : value < 0 ? 'error' : 'default';
    };

    const getPLIcon = (value: number) => {
        return value >= 0 ? <TrendingUpIcon fontSize="small" /> : <TrendingDownIcon fontSize="small" />;
    };

    // Calculate portfolio summary from backend data
    const portfolioSummary = positions.length > 0 ? {
        totalMarketValue: positions.reduce((sum, pos) => sum + pos.market_value, 0),
        totalCost: positions.reduce((sum, pos) => sum + pos.total_cost, 0),
        totalUnrealizedPL: positions.reduce((sum, pos) => sum + pos.unrealized_pl, 0),
        totalInceptionPL: positions.reduce((sum, pos) => sum + pos.inception_pl, 0),
        totalDTDPL: positions.reduce((sum, pos) => sum + pos.dtd_pl, 0),
        totalMTDPL: positions.reduce((sum, pos) => sum + pos.mtd_pl, 0),
        totalYTDPL: positions.reduce((sum, pos) => sum + pos.ytd_pl, 0),
    } : null;

    return (
        <Container maxWidth="xl" sx={{ width: '90%', mx: 'auto' }}>
            <Box sx={{ mb: 2 }}>
                <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 1 }}>
                    Portfolio View
                </Typography>

                <FormControl sx={{ minWidth: 300, mb: 2 }}>
                    <InputLabel>Select Portfolio</InputLabel>
                    <Select
                        value={selectedPortfolio}
                        label="Select Portfolio"
                        onChange={(e) => setSelectedPortfolio(e.target.value)}
                    >
                        {portfolios.map((portfolio) => (
                            <MenuItem key={portfolio._id} value={portfolio.portfolio_name}>
                                {portfolio.portfolio_name}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {selectedPortfolio && portfolioSummary && (
                <>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)', lg: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
                        <Card>
                            <CardContent sx={{ p: 2 }}>
                                <Typography variant="h6" color="primary" gutterBottom>
                                    Market Value
                                </Typography>
                                <Typography variant="h4">
                                    {formatCurrency(portfolioSummary.totalMarketValue)}
                                </Typography>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent sx={{ p: 2 }}>
                                <Typography variant="h6" color="text.secondary" gutterBottom>
                                    Total Cost
                                </Typography>
                                <Typography variant="h4">
                                    {formatCurrency(portfolioSummary.totalCost)}
                                </Typography>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent sx={{ p: 2 }}>
                                <Typography variant="h6" color="text.secondary" gutterBottom>
                                    Inception P&L
                                </Typography>
                                <Typography variant="h4" color={getPLColor(portfolioSummary.totalInceptionPL)}>
                                    {formatCurrency(portfolioSummary.totalInceptionPL)}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    Total P&L from inception
                                </Typography>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent sx={{ p: 2 }}>
                                <Typography variant="h6" color="text.secondary" gutterBottom>
                                    DTD P&L
                                </Typography>
                                <Typography variant="h4" color={getPLColor(portfolioSummary.totalDTDPL)}>
                                    {formatCurrency(portfolioSummary.totalDTDPL)}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    Day-to-date P&L
                                </Typography>
                            </CardContent>
                        </Card>
                    </Box>

                    <Alert severity="info" sx={{ mb: 3 }}>
                        <Typography variant="body2">
                            <strong>Note:</strong> Inception P&L shows the total P&L from inception for each position, calculated by the backend using current market prices.
                        </Typography>
                    </Alert>
                </>
            )}

            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                    <CircularProgress />
                </Box>
            ) : selectedPortfolio ? (
                <Paper sx={{ p: 1 }}>
                    <TableContainer>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Symbol</TableCell>
                                    <TableCell>Type</TableCell>
                                    <TableCell align="right">Quantity</TableCell>
                                    <TableCell align="right">Avg Cost</TableCell>
                                    <TableCell align="right">Current Price</TableCell>
                                    <TableCell align="right">Market Value</TableCell>
                                    <TableCell align="right">Inception P&L</TableCell>
                                    <TableCell align="right">DTD P&L</TableCell>
                                    <TableCell align="right">MTD P&L</TableCell>
                                    <TableCell align="right">YTD P&L</TableCell>
                                    <TableCell align="center">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {positions.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={11} align="center">
                                            <Typography variant="body1" color="text.secondary">
                                                No positions found for this portfolio
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    positions.map((position, index) => (
                                        <TableRow key={index} hover>
                                            <TableCell>
                                                <Typography variant="body1" fontWeight="medium">
                                                    {position.symbol}
                                                </Typography>
                                            </TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={position.instrument_type}
                                                    size="small"
                                                    color={position.instrument_type === 'STOCK' ? 'primary' : 'secondary'}
                                                />
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography variant="body2">
                                                    {position.position_quantity.toLocaleString()}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography variant="body2">
                                                    {formatCurrency(position.average_cost)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography variant="body2">
                                                    {formatCurrency(position.current_price)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography variant="body2">
                                                    {formatCurrency(position.market_value)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography color={getPLColor(position.inception_pl)}>
                                                    {formatCurrency(position.inception_pl)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography color={getPLColor(position.dtd_pl)}>
                                                    {formatCurrency(position.dtd_pl)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography color={getPLColor(position.mtd_pl)}>
                                                    {formatCurrency(position.mtd_pl)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <Typography color={getPLColor(position.ytd_pl)}>
                                                    {formatCurrency(position.ytd_pl)}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="center">
                                                <Tooltip title="Update Price">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => setPriceDialog({
                                                            open: true,
                                                            symbol: position.symbol,
                                                            currentPrice: position.current_price
                                                        })}
                                                    >
                                                        <EditIcon />
                                                    </IconButton>
                                                </Tooltip>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Paper>
            ) : null}

            {/* Price Update Dialog */}
            <Dialog open={priceDialog.open} onClose={() => setPriceDialog({ open: false, symbol: '', currentPrice: 0 })}>
                <DialogTitle>Update Price for {priceDialog.symbol}</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="New Price"
                        type="number"
                        fullWidth
                        variant="outlined"
                        value={newPrice}
                        onChange={(e) => setNewPrice(e.target.value)}
                        placeholder={priceDialog.currentPrice.toString()}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setPriceDialog({ open: false, symbol: '', currentPrice: 0 })}>
                        Cancel
                    </Button>
                    <Button onClick={handleUpdatePrice}>
                        Update
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default PortfolioView;
