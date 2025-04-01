import React from 'react';
import { Box, Typography } from '@mui/material';

export default function Journal() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Journal
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Record your thoughts and track your mood
      </Typography>
    </Box>
  );
} 