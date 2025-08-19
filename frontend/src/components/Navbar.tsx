import React, { useState } from 'react';
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    Box,
    IconButton,
    Menu,
    MenuItem,
} from '@mui/material';
import {
    Dashboard as DashboardIcon,
    AddCircle as AddCircleIcon,
    Assessment as AssessmentIcon,
    Home as HomeIcon,
    Settings as SettingsIcon,
    ArrowDropDown as ArrowDropDownIcon,
    Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [settingsAnchorEl, setSettingsAnchorEl] = useState<null | HTMLElement>(null);

    const menuItems = [
        { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
        { label: 'Trade Management', path: '/trade-entry', icon: <AddCircleIcon /> },
        { label: 'Portfolio View', path: '/portfolio-view', icon: <AssessmentIcon /> },
        { label: 'Portfolio Analytics', path: '/portfolio-analytics', icon: <AssessmentIcon /> },
        { label: 'AI Predictions', path: '/ai-predictions', icon: <PsychologyIcon /> },
    ];

    const settingsMenuItems = [
        { label: 'Portfolio Management', path: '/portfolio-management' },
        { label: 'Stock Management', path: '/stock-management' },
        { label: 'Options Management', path: '/option-management' },
    ];

    const handleSettingsClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setSettingsAnchorEl(event.currentTarget);
    };

    const handleSettingsClose = () => {
        setSettingsAnchorEl(null);
    };

    const handleSettingsMenuClick = (path: string) => {
        navigate(path);
        handleSettingsClose();
    };

    const isSettingsActive = settingsMenuItems.some(item => location.pathname === item.path);

    return (
        <AppBar position="static" sx={{ mb: 3 }}>
            <Toolbar>
                <IconButton
                    edge="start"
                    color="inherit"
                    onClick={() => navigate('/')}
                    sx={{ mr: 2 }}
                >
                    <HomeIcon />
                </IconButton>

                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    Investment Portfolio Tracker
                </Typography>

                <Box sx={{ display: 'flex', gap: 1 }}>
                    {menuItems.map((item) => (
                        <Button
                            key={item.path}
                            color="inherit"
                            onClick={() => navigate(item.path)}
                            startIcon={item.icon}
                            sx={{
                                backgroundColor: location.pathname === item.path ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                                '&:hover': {
                                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                },
                            }}
                        >
                            {item.label}
                        </Button>
                    ))}

                    {/* Settings Dropdown */}
                    <Button
                        color="inherit"
                        onClick={handleSettingsClick}
                        startIcon={<SettingsIcon />}
                        endIcon={<ArrowDropDownIcon />}
                        sx={{
                            backgroundColor: isSettingsActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                            '&:hover': {
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                            },
                        }}
                    >
                        Static Data
                    </Button>
                    <Menu
                        anchorEl={settingsAnchorEl}
                        open={Boolean(settingsAnchorEl)}
                        onClose={handleSettingsClose}
                        anchorOrigin={{
                            vertical: 'bottom',
                            horizontal: 'left',
                        }}
                        transformOrigin={{
                            vertical: 'top',
                            horizontal: 'left',
                        }}
                    >
                        {settingsMenuItems.map((item) => (
                            <MenuItem
                                key={item.path}
                                onClick={() => handleSettingsMenuClick(item.path)}
                                selected={location.pathname === item.path}
                            >
                                {item.label}
                            </MenuItem>
                        ))}
                    </Menu>
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default Navbar;
