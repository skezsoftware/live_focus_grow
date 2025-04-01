import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  Fade,
  Link,
} from '@mui/material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { keyframes } from '@mui/system';

const glowText = keyframes`
  0% { text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00; }
  50% { text-shadow: 0 0 15px #00ff00, 0 0 25px #00ff00; }
  100% { text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00; }
`;

const pulse = keyframes`
  0% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 255, 0, 0.5); }
  50% { transform: scale(1.02); box-shadow: 0 0 30px rgba(0, 255, 0, 0.7); }
  100% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 255, 0, 0.5); }
`;

export default function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('http://localhost:5001/api/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || 'Login failed');
      }

      // Store the token
      localStorage.setItem('token', data.access_token);
      
      // Check if user has completed setup
      const userResponse = await fetch('http://localhost:5001/api/user/profile', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      if (!userResponse.ok) {
        if (userResponse.status === 401) {
          throw new Error('Invalid credentials');
        }
        throw new Error('Failed to fetch user profile');
      }

      const userData = await userResponse.json();
      
      // Navigate to dashboard
      navigate('/dashboard');
    } catch (error) {
      setError(error.message || 'Login failed. Please try again.');
      console.error('Login failed:', error);
    }
  };

  const textFieldStyle = {
    mb: 2,
    '& .MuiOutlinedInput-root': {
      color: 'white',
      '& fieldset': {
        borderColor: 'rgba(0, 255, 0, 0.5)',
      },
      '&:hover fieldset': {
        borderColor: '#00ff00',
      },
      '&.Mui-focused fieldset': {
        borderColor: '#00ff00',
      },
    },
    '& .MuiInputLabel-root': {
      color: '#00ff00',
    },
    '& .MuiInputLabel-root.Mui-focused': {
      color: '#00ff00',
    },
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      backgroundColor: '#121212',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      p: 3,
      backgroundImage: 'radial-gradient(circle at center, rgba(0, 255, 0, 0.1) 0%, rgba(0, 0, 0, 0) 70%)',
    }}>
      <Paper sx={{
        p: 4,
        maxWidth: 400,
        width: '100%',
        backgroundColor: 'rgba(0,0,0,0.9)',
        border: '1px solid rgba(0, 255, 0, 0.1)',
        boxShadow: '0 0 20px rgba(0, 255, 0, 0.1)',
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 0 30px rgba(0, 255, 0, 0.2)',
        },
      }}>
        <Typography variant="h4" sx={{
          textAlign: 'center',
          mb: 4,
          color: '#00ff00',
          fontFamily: 'Impact, sans-serif',
          textTransform: 'uppercase',
          animation: `${glowText} 2s infinite`,
          letterSpacing: '1px',
        }}>
          Login
        </Typography>

        {error && (
          <Fade in={!!error}>
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                color: '#ff0000',
                border: '1px solid rgba(255, 0, 0, 0.3)',
                '& .MuiAlert-icon': {
                  color: '#ff0000',
                }
              }}
            >
              {error}
            </Alert>
          </Fade>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            margin="normal"
            required
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            sx={textFieldStyle}
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            margin="normal"
            required
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            sx={textFieldStyle}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{
              mt: 2,
              py: 1.5,
              backgroundColor: '#00ff00',
              color: '#000000',
              fontFamily: 'Impact, sans-serif',
              fontSize: '1.1rem',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              border: '2px solid #00ff00',
              boxShadow: '0 0 20px rgba(0, 255, 0, 0.5)',
              animation: `${pulse} 3s infinite`,
              '&:hover': {
                backgroundColor: '#00cc00',
                boxShadow: '0 0 30px rgba(0, 255, 0, 0.7)',
              }
            }}
          >
            Enter the Game
          </Button>

          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Link
              component={RouterLink}
              to="/register"
              sx={{
                color: '#00ff00',
                textDecoration: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                }
              }}
            >
              New player? Create an account
            </Link>
          </Box>
        </form>
      </Paper>
    </Box>
  );
} 