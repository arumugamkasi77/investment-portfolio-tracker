import React, { useState } from 'react';
import {
    Box,
    Button,
    TextField,
    Typography,
    Chip,
    IconButton,
    Tooltip,
    Alert
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    PlayArrow as PlayIcon,
    Pause as PauseIcon,
    Settings as SettingsIcon
} from '@mui/icons-material';
import { useAutoRefresh } from '../contexts/AutoRefreshContext';

interface AutoRefreshControlProps {
    onManualRefresh: () => void;
    isRefreshing?: boolean;
    showLastRefreshTime?: boolean;
}

const AutoRefreshControl: React.FC<AutoRefreshControlProps> = ({
    onManualRefresh,
    isRefreshing = false,
    showLastRefreshTime = true
}) => {
    const { isEnabled, intervalSeconds, toggleAutoRefresh, setIntervalSeconds, lastRefreshTime } = useAutoRefresh();
    const [showIntervalInput, setShowIntervalInput] = useState(false);
    const [tempInterval, setTempInterval] = useState(intervalSeconds.toString());

    const handleIntervalChange = () => {
        const newInterval = parseInt(tempInterval);
        if (!isNaN(newInterval) && newInterval >= 1 && newInterval <= 300) {
            setIntervalSeconds(newInterval);
            setShowIntervalInput(false);
        }
    };

    const handleKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter') {
            handleIntervalChange();
        } else if (event.key === 'Escape') {
            setTempInterval(intervalSeconds.toString());
            setShowIntervalInput(false);
        }
    };

    const formatLastRefreshTime = () => {
        if (!lastRefreshTime) return 'Never';
        const now = new Date();
        const diffMs = now.getTime() - lastRefreshTime.getTime();
        const diffSecs = Math.floor(diffMs / 1000);

        if (diffSecs < 60) return `${diffSecs}s ago`;
        if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
        return `${Math.floor(diffSecs / 3600)}h ago`;
    };

    return (
        <Box sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            minWidth: '280px', // Fixed width to prevent layout shifts
            justifyContent: 'flex-end'
        }}>
            <Button
                variant={isEnabled ? "contained" : "outlined"}
                color={isEnabled ? "success" : "inherit"}
                startIcon={isEnabled ? <PlayIcon /> : <PauseIcon />}
                onClick={toggleAutoRefresh}
                size="small"
                sx={{ minWidth: '100px' }} // Fixed button width
            >
                {isEnabled ? "Auto-ON" : "Auto-OFF"}
            </Button>

            <Chip
                label={`${intervalSeconds}s`}
                size="small"
                onClick={() => {
                    const newInterval = prompt('Enter refresh interval (1-300 seconds):', intervalSeconds.toString());
                    if (newInterval) {
                        const seconds = parseInt(newInterval);
                        if (!isNaN(seconds) && seconds >= 1 && seconds <= 300) {
                            setIntervalSeconds(seconds);
                        }
                    }
                }}
                sx={{
                    cursor: 'pointer',
                    minWidth: '50px', // Fixed chip width
                    textAlign: 'center'
                }}
            />

            <Button
                variant="outlined"
                size="small"
                onClick={onManualRefresh}
                disabled={isRefreshing}
                sx={{ minWidth: '80px' }} // Fixed button width
            >
                {isRefreshing ? "Updating..." : "Refresh Now"}
            </Button>

            {showLastRefreshTime && lastRefreshTime && (
                <Typography variant="caption" color="text.secondary" sx={{ minWidth: '120px', textAlign: 'right' }}>
                    Last: {lastRefreshTime.toLocaleTimeString()}
                </Typography>
            )}
        </Box>
    );
};

export default AutoRefreshControl;
