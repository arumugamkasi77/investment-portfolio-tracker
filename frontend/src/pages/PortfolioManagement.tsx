import React, { useState, useEffect } from 'react';
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
    InputAdornment,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
} from '@mui/material';
import {
    Add as AddIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Search as SearchIcon,
    FilterList as FilterIcon,
} from '@mui/icons-material';
import { portfolioApi } from '../services/api';

interface PortfolioStatic {
    _id?: string;
    name: string;
    owner: string;
    description?: string;
    created_at?: string;
    updated_at?: string;
}

const PortfolioManagement: React.FC = () => {
    const [portfolios, setPortfolios] = useState<PortfolioStatic[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitLoading, setSubmitLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [editingPortfolio, setEditingPortfolio] = useState<PortfolioStatic | null>(null);

    const [formData, setFormData] = useState<PortfolioStatic>({
        name: '',
        owner: '',
        description: '',
    });

    // Search and filter states
    const [searchTerm, setSearchTerm] = useState('');
    const [filterOwner, setFilterOwner] = useState<string>('');

    useEffect(() => {
        loadPortfolios();
    }, []);

    const loadPortfolios = async () => {
        try {
            setLoading(true);
            const response = await portfolioApi.getStaticPortfolios();
            setPortfolios(response.data || []);
        } catch (err: any) {
            console.error('Error loading portfolios:', err);
            setError('Failed to load portfolios');
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
            if (editingPortfolio) {
                // Update existing portfolio
                await portfolioApi.updatePortfolio(editingPortfolio._id!, formData);
                setSuccess('Portfolio updated successfully!');
            } else {
                // Create new portfolio
                await portfolioApi.createPortfolio(formData);
                setSuccess('Portfolio created successfully!');
            }

            handleCloseDialog();
            loadPortfolios();
        } catch (err: any) {
            console.error('Error saving portfolio:', err);
            setError(err.response?.data?.detail || 'Failed to save portfolio');
        } finally {
            setSubmitLoading(false);
        }
    };

    const handleEdit = (portfolio: PortfolioStatic) => {
        setEditingPortfolio(portfolio);
        setFormData({
            name: portfolio.name,
            owner: portfolio.owner,
            description: portfolio.description || '',
        });
        setOpenDialog(true);
    };

    const handleDelete = async (portfolioId: string) => {
        if (!window.confirm('Are you sure you want to delete this portfolio?')) {
            return;
        }

        try {
            await portfolioApi.deletePortfolio(portfolioId);
            setSuccess('Portfolio deleted successfully!');
            loadPortfolios();
        } catch (err: any) {
            console.error('Error deleting portfolio:', err);
            setError('Failed to delete portfolio');
        }
    };

    const handleOpenDialog = () => {
        setEditingPortfolio(null);
        setFormData({ name: '', owner: '', description: '' });
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingPortfolio(null);
        setFormData({ name: '', owner: '', description: '' });
        setError(null);
    };

    const handleInputChange = (field: keyof PortfolioStatic, value: string) => {
        setFormData(prev => ({
            ...prev,
            [field]: value,
        }));
    };

    // Filter portfolios based on search and filter criteria
    const filteredPortfolios = portfolios.filter(portfolio => {
        const matchesSearch = searchTerm === '' ||
            portfolio.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            portfolio.owner.toLowerCase().includes(searchTerm.toLowerCase()) ||
            portfolio.description?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesOwner = filterOwner === '' || portfolio.owner === filterOwner;

        return matchesSearch && matchesOwner;
    });

    return (
        <Container maxWidth="xl" sx={{ width: '90%', mx: 'auto', py: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h4" component="h1">
                    Portfolio Management
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleOpenDialog}
                >
                    Add Portfolio
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
                <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' } }}>
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

                    {/* Owner Filter */}
                    <FormControl size="small">
                        <InputLabel>Owner</InputLabel>
                        <Select
                            value={filterOwner}
                            onChange={(e) => setFilterOwner(e.target.value)}
                            label="Owner"
                        >
                            <MenuItem value="">All Owners</MenuItem>
                            {Array.from(new Set(portfolios.map(p => p.owner))).map((owner) => (
                                <MenuItem key={owner} value={owner}>
                                    {owner}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Box>

                {/* Results Count */}
                <Box sx={{ mt: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                        Showing {filteredPortfolios.length} of {portfolios.length} portfolios
                    </Typography>
                    <Button
                        size="small"
                        onClick={() => {
                            setSearchTerm('');
                            setFilterOwner('');
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
                                    <TableCell>Portfolio Name</TableCell>
                                    <TableCell>Owner</TableCell>
                                    <TableCell>Description</TableCell>
                                    <TableCell>Created Date</TableCell>
                                    <TableCell align="center">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {filteredPortfolios.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} align="center">
                                            <Typography variant="body1" color="text.secondary">
                                                {portfolios.length === 0
                                                    ? 'No portfolios found. Create your first portfolio!'
                                                    : 'No portfolios match your current filters. Try adjusting your search criteria.'
                                                }
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredPortfolios.map((portfolio) => (
                                        <TableRow key={portfolio._id}>
                                            <TableCell>{portfolio.name}</TableCell>
                                            <TableCell>{portfolio.owner}</TableCell>
                                            <TableCell>{portfolio.description || '-'}</TableCell>
                                            <TableCell>
                                                {portfolio.created_at
                                                    ? new Date(portfolio.created_at).toLocaleDateString()
                                                    : '-'
                                                }
                                            </TableCell>
                                            <TableCell align="center">
                                                <IconButton
                                                    color="primary"
                                                    onClick={() => handleEdit(portfolio)}
                                                    size="small"
                                                >
                                                    <EditIcon />
                                                </IconButton>
                                                <IconButton
                                                    color="error"
                                                    onClick={() => handleDelete(portfolio._id!)}
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

            {/* Add/Edit Portfolio Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {editingPortfolio ? 'Edit Portfolio' : 'Add New Portfolio'}
                </DialogTitle>
                <DialogContent>
                    <Box component="form" onSubmit={handleSubmit} sx={{ pt: 2 }}>
                        <Box sx={{ display: 'grid', gap: 3 }}>
                            <TextField
                                label="Portfolio Name"
                                value={formData.name}
                                onChange={(e) => handleInputChange('name', e.target.value)}
                                required
                                fullWidth
                                helperText="Unique name for the portfolio"
                            />

                            <TextField
                                label="Owner"
                                value={formData.owner}
                                onChange={(e) => handleInputChange('owner', e.target.value)}
                                required
                                fullWidth
                                helperText="Owner or manager of the portfolio"
                            />

                            <TextField
                                label="Description"
                                value={formData.description}
                                onChange={(e) => handleInputChange('description', e.target.value)}
                                fullWidth
                                multiline
                                rows={3}
                                helperText="Optional description of the portfolio"
                            />
                        </Box>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>Cancel</Button>
                    <Button
                        onClick={handleSubmit}
                        variant="contained"
                        disabled={submitLoading || !formData.name || !formData.owner}
                    >
                        {submitLoading ? (
                            <CircularProgress size={24} />
                        ) : (
                            editingPortfolio ? 'Update' : 'Create'
                        )}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default PortfolioManagement;
