import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Container,
    Typography,
    Box,
    Card,
    CardContent,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Alert,
    CircularProgress,
    IconButton,
    Tooltip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Chip,
} from '@mui/material';
import {
    Edit as EditIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import { portfolioApi } from '../services/api';
import { useAutoRefresh } from '../contexts/AutoRefreshContext';
import AutoRefreshControl from '../components/AutoRefreshControl';

// DOM-only P&L value component - bypasses React entirely
const PLValueCell = React.memo(({ value, label, rowIndex, columnIndex }: {
    value: number;
    label: string;
    rowIndex: number;
    columnIndex: number;
}) => {
    const formatCurrency = (value: number): string => {
        if (value === null || value === undefined || isNaN(value)) return '$0.00';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(value);
    };

    const getPLColor = (value: number): string => {
        if (value === null || value === undefined || isNaN(value)) return 'text.secondary';
        return value >= 0 ? 'success.main' : 'error.main';
    };

    return (
        <TableCell
            align="right"
            sx={{
                minWidth: '120px',
                height: '60px',
                verticalAlign: 'middle',
                position: 'relative'
            }}
        >
            <Box sx={{
                position: 'absolute',
                top: '50%',
                right: '16px',
                transform: 'translateY(-50%)',
                width: '100%',
                textAlign: 'right'
            }}>
                <Typography
                    id={`pl-cell-${rowIndex}-${columnIndex}`}
                    sx={{
                        color: getPLColor(value),
                        fontSize: '0.875rem',
                        lineHeight: 1,
                        transition: 'color 0.3s ease-in-out'
                    }}
                >
                    {formatCurrency(value)}
                </Typography>
            </Box>
        </TableCell>
    );
}, () => {
    // Never re-render this component
    return true;
});

PLValueCell.displayName = 'PLValueCell';

// Memoized position row component to prevent unnecessary re-renders
const PositionRow = React.memo(({ position, onEditPrice, rowIndex }: {
    position: any;
    onEditPrice: (symbol: string, currentPrice: number) => void;
    rowIndex: number;
}) => {
    const formatCurrency = (value: number): string => {
        if (value === null || value === undefined || isNaN(value)) return '$0.00';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(value);
    };

    return (
        <TableRow hover sx={{ transition: 'background-color 0.2s ease-in-out' }}>
            <TableCell sx={{ minWidth: '80px', height: '60px', verticalAlign: 'middle' }}>
                <Typography variant="body1" fontWeight="medium">
                    {position.symbol}
                </Typography>
            </TableCell>
            <TableCell sx={{ minWidth: '80px', height: '60px', verticalAlign: 'middle' }}>
                <Chip
                    label={position.instrument_type}
                    size="small"
                    color={position.instrument_type === 'STOCK' ? 'primary' : 'secondary'}
                />
            </TableCell>
            <TableCell align="right" sx={{ minWidth: '100px', height: '60px', verticalAlign: 'middle' }}>
                <Typography variant="body2">
                    {position.position_quantity?.toLocaleString() || '0'}
                </Typography>
            </TableCell>
            <TableCell align="right" sx={{ minWidth: '100px', height: '60px', verticalAlign: 'middle' }}>
                <Typography variant="body2">
                    {formatCurrency(position.average_cost)}
                </Typography>
            </TableCell>
            <TableCell align="right" sx={{ minWidth: '100px', height: '60px', verticalAlign: 'middle' }}>
                <Box>
                    <Typography variant="body2" id={`current-price-${rowIndex}`}>
                        {formatCurrency(position.current_price)}
                    </Typography>
                    {position.price_type && position.price_type !== 'regular_market' && (
                        <Chip
                            label={position.price_type.replace('_', ' ').toUpperCase()}
                            size="small"
                            color={position.price_type === 'pre_market' ? 'warning' : 'info'}
                            sx={{
                                fontSize: '0.6rem',
                                height: '16px',
                                mt: 0.5,
                                '& .MuiChip-label': { px: 0.5 }
                            }}
                        />
                    )}
                </Box>
            </TableCell>
            <TableCell align="right" sx={{ minWidth: '120px', height: '60px', verticalAlign: 'middle' }}>
                <Typography variant="body2" id={`market-value-${rowIndex}`}>
                    {formatCurrency(position.market_value)}
                </Typography>
            </TableCell>

            {/* Individual P&L cells that update independently */}
            <PLValueCell value={position.inception_pl} label="Inception P&L" rowIndex={rowIndex} columnIndex={0} />
            <PLValueCell value={position.dtd_pl} label="DTD P&L" rowIndex={rowIndex} columnIndex={1} />
            <PLValueCell value={position.mtd_pl} label="MTD P&L" rowIndex={rowIndex} columnIndex={2} />
            <PLValueCell value={position.ytd_pl} label="YTD P&L" rowIndex={rowIndex} columnIndex={3} />

            <TableCell align="center" sx={{ minWidth: '80px', height: '60px', verticalAlign: 'middle' }}>
                <Tooltip title="Update Price">
                    <IconButton
                        size="small"
                        onClick={() => onEditPrice(position.symbol, position.current_price)}
                    >
                        <EditIcon />
                    </IconButton>
                </Tooltip>
            </TableCell>
        </TableRow>
    );
}, (prevProps, nextProps) => {
    // Only re-render if non-P&L values change
    return (
        prevProps.position.symbol === nextProps.position.symbol &&
        prevProps.position.position_quantity === nextProps.position.position_quantity &&
        prevProps.position.average_cost === nextProps.position.average_cost &&
        prevProps.position.current_price === nextProps.position.current_price &&
        prevProps.position.market_value === nextProps.position.market_value
        // P&L values are handled by individual PLValueCell components
    );
});

PositionRow.displayName = 'PositionRow';

const PortfolioView: React.FC = () => {
    const [portfolios, setPortfolios] = useState<any[]>([]);
    const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
    const [positions, setPositions] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [portfolioSummary, setPortfolioSummary] = useState<any>(null);
    const [portfolioTotals, setPortfolioTotals] = useState<any>({
        marketValue: 0,
        totalCost: 0,
        totalPL: 0
    });
    const { isEnabled, intervalSeconds, updateLastRefreshTime } = useAutoRefresh();
    const [isRefreshing, setIsRefreshing] = useState(false); // Separate state for smooth updates
    const [priceDialog, setPriceDialog] = useState({
        open: false,
        symbol: '',
        currentPrice: 0,
    });
    const [newPrice, setNewPrice] = useState<string>('');

    // Function to directly update DOM values without React re-renders
    const updatePLValueInDOM = useCallback((rowIndex: number, columnIndex: number, newValue: number) => {
        const element = document.getElementById(`pl-cell-${rowIndex}-${columnIndex}`);
        if (element) {
            const formatCurrency = (value: number): string => {
                if (value === null || value === undefined || isNaN(value)) return '$0.00';
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                }).format(value);
            };

            const getPLColor = (value: number): string => {
                if (value === null || value === undefined || isNaN(value)) return 'text.secondary';
                return value >= 0 ? 'success.main' : 'error.main';
            };

            element.textContent = formatCurrency(newValue);
            element.style.color = getPLColor(newValue);
        }
    }, []);

    // Function to update market data fields during silent refresh
    const updateMarketDataInDOM = useCallback((rowIndex: number, position: any) => {
        console.log(`🔄 DEBUG: updateMarketDataInDOM called for row ${rowIndex}, symbol ${position.symbol}`);

        const formatCurrency = (value: number): string => {
            if (value === null || value === undefined || isNaN(value)) return '$0.00';
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
            }).format(value);
        };

        // Update Current Price
        const currentPriceElement = document.getElementById(`current-price-${rowIndex}`);
        if (currentPriceElement) {
            console.log(`✅ DEBUG: Updating current price for ${position.symbol} to ${formatCurrency(position.current_price)}`);
            currentPriceElement.textContent = formatCurrency(position.current_price);
        } else {
            console.log(`❌ DEBUG: Could not find current-price-${rowIndex} element for ${position.symbol}`);
        }

        // Update Market Value
        const marketValueElement = document.getElementById(`market-value-${rowIndex}`);
        if (marketValueElement) {
            console.log(`✅ DEBUG: Updating market value for ${position.symbol} to ${formatCurrency(position.market_value)}`);
            marketValueElement.textContent = formatCurrency(position.market_value);
        } else {
            console.log(`❌ DEBUG: Could not find market-value-${rowIndex} element for ${position.symbol}`);
        }

        // Update Inception P&L (column 0)
        updatePLValueInDOM(rowIndex, 0, position.inception_pl);
    }, [updatePLValueInDOM]);

    // Function to update portfolio totals during silent refresh
    const updatePortfolioTotalsInDOM = useCallback((totals: any) => {
        const formatCurrency = (value: number): string => {
            if (value === null || value === undefined || isNaN(value)) return '$0.00';
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
            }).format(value);
        };

        // Update Total Market Value
        const marketValueElement = document.getElementById('total-market-value');
        if (marketValueElement) {
            marketValueElement.textContent = formatCurrency(totals.marketValue);
        }

        // Update Total Cost
        const totalCostElement = document.getElementById('total-cost');
        if (totalCostElement) {
            totalCostElement.textContent = formatCurrency(totals.totalCost);
        }

        // Update Total P&L
        const totalPLElement = document.getElementById('total-pl');
        if (totalPLElement) {
            totalPLElement.textContent = formatCurrency(totals.totalPL);
        }
    }, []);

    useEffect(() => {
        loadPortfolios();
    }, []);

    const loadPortfolioPositions = useCallback(async (isSilentRefresh = false) => {
        if (!selectedPortfolio) return;

        try {
            if (!isSilentRefresh) {
                setLoading(true);
            } else {
                setIsRefreshing(true);
            }
            setError(null);

            // Use single consolidated endpoint to eliminate race conditions
            const url = isSilentRefresh
                ? `http://localhost:8000/portfolios/${selectedPortfolio}/positions-with-analysis?force_fresh=true`
                : `http://localhost:8000/portfolios/${selectedPortfolio}/positions-with-analysis`;

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch portfolio with analysis');
            }

            const data = await response.json();

            // Extract positions and portfolio totals from single response
            const mergedPositions = data.positions;
            if (data.portfolio_totals) {
                // Map the new consolidated endpoint structure to the expected format
                const mappedSummary = {
                    current_total_pl: data.portfolio_totals.total_inception_pl,
                    dtd_pl: data.portfolio_totals.total_dtd_pl,
                    mtd_pl: data.portfolio_totals.total_mtd_pl,
                    ytd_pl: data.portfolio_totals.total_ytd_pl,
                    last_working_day_total_pl: data.portfolio_totals.total_inception_pl - data.portfolio_totals.total_dtd_pl,
                    month_start_total_pl: data.portfolio_totals.total_inception_pl - data.portfolio_totals.total_mtd_pl,
                    year_start_total_pl: data.portfolio_totals.total_inception_pl - data.portfolio_totals.total_ytd_pl,
                    analysis_date: data.analysis_date
                };
                setPortfolioSummary(mappedSummary);

                // Also set portfolio totals for the fallback display
                setPortfolioTotals({
                    marketValue: data.portfolio_totals.total_market_value,
                    totalCost: data.portfolio_totals.total_cost,
                    totalPL: data.portfolio_totals.total_unrealized_pl
                });
            }

            if (isSilentRefresh) {
                // PROFESSIONAL BEHAVIOR: Only update when we have fresh, valid market data
                // No loading indicators - keep previous values if new data isn't ready

                // PROFESSIONAL AUTO-REFRESH: Only update when we have valid, fresh market data
                mergedPositions.forEach((position: any, rowIndex: number) => {
                    // Only update if we have valid market data (not fallback prices)
                    if (position.current_price && position.current_price > 0 && position.current_price !== position.average_cost) {
                        // Get current displayed price to compare
                        const currentPriceElement = document.getElementById(`current-price-${rowIndex}`);
                        const currentDisplayedPrice = currentPriceElement && currentPriceElement.textContent ? parseFloat(currentPriceElement.textContent.replace(/[$,]/g, '')) : null;

                        // Only update if price has actually changed significantly
                        if (currentDisplayedPrice === null || Math.abs(position.current_price - currentDisplayedPrice) > 0.01) {
                            // Update market data (current price, market value, inception P&L)
                            updateMarketDataInDOM(rowIndex, position);
                            // Update P&L values
                            updatePLValueInDOM(rowIndex, 1, position.dtd_pl);
                            updatePLValueInDOM(rowIndex, 2, position.mtd_pl);
                            updatePLValueInDOM(rowIndex, 3, position.ytd_pl);
                        }
                    }
                    // If no valid data, keep the previous value (professional behavior)
                });

                // Update portfolio totals with valid data
                const validPositions = mergedPositions.filter((pos: any) => pos.current_price && pos.current_price > 0);
                if (validPositions.length > 0) {
                    const totals = {
                        marketValue: validPositions.reduce((sum: number, pos: any) => sum + (pos.market_value || 0), 0),
                        totalCost: validPositions.reduce((sum: number, pos: any) => sum + (pos.total_cost || 0), 0),
                        totalPL: validPositions.reduce((sum: number, pos: any) => sum + (pos.unrealized_pl || 0), 0)
                    };
                    updatePortfolioTotalsInDOM(totals);
                }
            } else {
                // For manual refresh, update everything normally
                setPositions(mergedPositions);
            }
        } catch (err: any) {
            console.error('Error loading portfolio positions:', err);
            if (!isSilentRefresh) {
                setError(err.response?.data?.detail || err.message || 'Failed to load portfolio positions');
            }
        } finally {
            if (!isSilentRefresh) {
                setLoading(false);
            } else {
                setIsRefreshing(false);
            }
        }
    }, [selectedPortfolio, updatePLValueInDOM, updateMarketDataInDOM, updatePortfolioTotalsInDOM]);

    useEffect(() => {
        if (selectedPortfolio) {
            loadPortfolioPositions();
        }
    }, [selectedPortfolio, loadPortfolioPositions]);

    // Auto-refresh effect - use silent refresh for smooth updates
    useEffect(() => {
        if (!isEnabled || !selectedPortfolio) {
            return;
        }

        const interval = setInterval(() => {
            loadPortfolioPositions(true); // Silent refresh
            updateLastRefreshTime();
        }, intervalSeconds * 1000);

        return () => {
            clearInterval(interval);
        };
    }, [isEnabled, intervalSeconds, selectedPortfolio, updateLastRefreshTime, loadPortfolioPositions]);

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
        if (value === null || value === undefined || isNaN(value)) return '$0.00';
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

    // Portfolio totals are now managed via state from the consolidated endpoint

    // Memoize the positions array to prevent unnecessary re-renders
    const memoizedPositions = useMemo(() => positions, [positions]);

    // Portfolio summary is now loaded from enhanced snapshots backend

    return (
        <Container maxWidth="xl">
            <Typography variant="h4" component="h1" gutterBottom>
                Portfolio View
            </Typography>

            {/* Auto-refresh control moved to top-right */}
            <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 3
            }}>
                <Box sx={{ flex: 1 }}>
                    <FormControl fullWidth>
                        <InputLabel>Select Portfolio</InputLabel>
                        <Select value={selectedPortfolio} onChange={(e) => setSelectedPortfolio(e.target.value)} label="Select Portfolio">
                            {portfolios.map((portfolio) => (<MenuItem key={portfolio.portfolio_name} value={portfolio.portfolio_name}>{portfolio.portfolio_name}</MenuItem>))}
                        </Select>
                    </FormControl>
                </Box>

                <Box sx={{ ml: 2 }}>
                    <AutoRefreshControl
                        onManualRefresh={loadPortfolioPositions}
                        isRefreshing={loading}
                        showLastRefreshTime={true}
                    />
                </Box>
            </Box>

            {/* Refresh status indicator - positioned in top-right corner to avoid jumping */}
            {isRefreshing && (
                <Box sx={{
                    position: 'fixed',
                    top: 20,
                    right: 20,
                    zIndex: 1000,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    color: 'white',
                    padding: '8px 12px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    opacity: 0.9,
                    transition: 'opacity 0.3s ease-in-out',
                    pointerEvents: 'none'
                }}>
                    🔄 Updating...
                </Box>
            )}

            {/* Portfolio Summary Section */}
            {portfolioSummary && (
                <Card sx={{
                    mb: 3,
                    p: 3,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    transition: 'all 0.3s ease-in-out'
                }}>
                    <Typography variant="h5" component="h2" gutterBottom>
                        Portfolio Summary - {selectedPortfolio}
                    </Typography>
                    <Box sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
                        gap: 2
                    }}>
                        <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="h6" sx={{ opacity: 0.9 }}>Total Portfolio P&L</Typography>
                            <Typography variant="h4" sx={{
                                fontWeight: 'bold',
                                color: (portfolioSummary?.current_total_pl || 0) >= 0 ? '#4caf50' : '#f44336',
                                transition: 'color 0.3s ease-in-out'
                            }}>
                                ${(portfolioSummary?.current_total_pl || 0).toLocaleString()}
                            </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="h6" sx={{ opacity: 0.9 }}>Day-to-Date P&L</Typography>
                            <Typography variant="h4" sx={{
                                fontWeight: 'bold',
                                color: (portfolioSummary?.dtd_pl || 0) >= 0 ? '#4caf50' : '#f44336',
                                transition: 'color 0.3s ease-in-out'
                            }}>
                                ${(portfolioSummary?.dtd_pl || 0).toLocaleString()}
                            </Typography>
                            <Typography variant="caption" sx={{ opacity: 0.8 }}>
                                vs {(portfolioSummary?.last_working_day_total_pl || 0) ? `$${(portfolioSummary?.last_working_day_total_pl || 0).toLocaleString()}` : '$0'} (Last Working Day)
                            </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="h6" sx={{ opacity: 0.9 }}>Month-to-Date P&L</Typography>
                            <Typography variant="h4" sx={{
                                fontWeight: 'bold',
                                color: (portfolioSummary?.mtd_pl || 0) >= 0 ? '#4caf50' : '#f44336',
                                transition: 'color 0.3s ease-in-out'
                            }}>
                                ${(portfolioSummary?.mtd_pl || 0).toLocaleString()}
                            </Typography>
                            <Typography variant="caption" sx={{ opacity: 0.8 }}>
                                vs {(portfolioSummary?.month_start_total_pl || 0) ? `$${(portfolioSummary?.month_start_total_pl || 0).toLocaleString()}` : '$0'} (Month Start)
                            </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="h6" sx={{ opacity: 0.9 }}>Year-to-Date P&L</Typography>
                            <Typography variant="h4" sx={{
                                fontWeight: 'bold',
                                color: (portfolioSummary?.ytd_pl || 0) >= 0 ? '#4caf50' : '#f44336',
                                transition: 'color 0.3s ease-in-out'
                            }}>
                                ${(portfolioSummary?.ytd_pl || 0).toLocaleString()}
                            </Typography>
                            <Typography variant="caption" sx={{ opacity: 0.8 }}>
                                vs {(portfolioSummary?.year_start_total_pl || 0) ? `$${(portfolioSummary?.year_start_total_pl || 0).toLocaleString()}` : '$0'} (Year Start)
                            </Typography>
                        </Box>
                    </Box>
                    <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', mt: 2, opacity: 0.7 }}>
                        Analysis Date: {portfolioSummary?.analysis_date || 'N/A'}
                    </Typography>
                </Card>
            )}

            {/* Fallback Portfolio Summary (when enhanced data not loaded) */}
            {!portfolioSummary && positions.length > 0 && (
                <Card sx={{ mb: 3, p: 3, backgroundColor: '#f5f5f5' }}>
                    <Typography variant="h6" gutterBottom sx={{ color: '#666', fontWeight: 'bold' }}>
                        📊 Basic Portfolio Summary - {selectedPortfolio}
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
                        <Box textAlign="center">
                            <Typography variant="h5" id="total-market-value" sx={{
                                color: (portfolioTotals?.marketValue || 0) >= 0 ? '#2e7d32' : '#d32f2f',
                                fontWeight: 'bold'
                            }}>
                                ${(portfolioTotals?.marketValue || 0).toLocaleString()}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                Total Market Value
                            </Typography>
                        </Box>
                        <Box textAlign="center">
                            <Typography variant="h5" id="total-cost" sx={{
                                color: (portfolioTotals?.totalCost || 0) >= 0 ? '#2e7d32' : '#d32f2f',
                                fontWeight: 'bold'
                            }}>
                                ${(portfolioTotals?.totalCost || 0).toLocaleString()}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                Total Cost
                            </Typography>
                        </Box>
                        <Box textAlign="center">
                            <Typography variant="h5" id="total-pl" sx={{
                                color: (portfolioTotals?.totalPL || 0) >= 0 ? '#2e7d32' : '#d32f2f',
                                fontWeight: 'bold'
                            }}>
                                ${(portfolioTotals?.totalPL || 0).toLocaleString()}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                Total Unrealized P&L
                            </Typography>
                        </Box>
                    </Box>
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
                        Enhanced P&L data loading... DTD/MTD/YTD calculations will appear here once loaded.
                    </Typography>
                </Card>
            )}

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
                                    {formatCurrency(portfolioTotals?.marketValue || 0)}
                                </Typography>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent sx={{ p: 2 }}>
                                <Typography variant="h6" color="text.secondary" gutterBottom>
                                    Total Cost
                                </Typography>
                                <Typography variant="h4">
                                    {formatCurrency(portfolioTotals?.totalCost || 0)}
                                </Typography>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent sx={{ p: 2 }}>
                                <Typography variant="h6" color="text.secondary" gutterBottom>
                                    Inception P&L
                                </Typography>
                                <Typography variant="h4" color={getPLColor(portfolioSummary.current_total_pl)}>
                                    {formatCurrency(portfolioSummary.current_total_pl)}
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
                                <Typography variant="h4" color={getPLColor(portfolioSummary.dtd_pl)}>
                                    {formatCurrency(portfolioSummary.dtd_pl)}
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
                    <TableContainer sx={{ maxHeight: '600px', overflow: 'auto' }}>
                        <Table size="small" stickyHeader>
                            <TableHead>
                                <TableRow>
                                    <TableCell sx={{ minWidth: '80px', backgroundColor: 'background.paper' }}>Symbol</TableCell>
                                    <TableCell sx={{ minWidth: '80px', backgroundColor: 'background.paper' }}>Type</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '100px', backgroundColor: 'background.paper' }}>Quantity</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '100px', backgroundColor: 'background.paper' }}>Avg Cost</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '100px', backgroundColor: 'background.paper' }}>Current Price</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '120px', backgroundColor: 'background.paper' }}>Market Value</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '120px', backgroundColor: 'background.paper' }}>Inception P&L</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '120px', backgroundColor: 'background.paper' }}>DTD P&L</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '120px', backgroundColor: 'background.paper' }}>MTD P&L</TableCell>
                                    <TableCell align="right" sx={{ minWidth: '120px', backgroundColor: 'background.paper' }}>YTD P&L</TableCell>
                                    <TableCell align="center" sx={{ minWidth: '80px', backgroundColor: 'background.paper' }}>Actions</TableCell>
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
                                    memoizedPositions.map((position, index) => (
                                        <PositionRow
                                            key={`${position.symbol}-${index}`}
                                            position={position}
                                            rowIndex={index}
                                            onEditPrice={(symbol, currentPrice) => setPriceDialog({ open: true, symbol, currentPrice })}
                                        />
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
