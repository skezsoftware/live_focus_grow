import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Card,
  IconButton,
  Paper,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  LinearProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { keyframes } from '@mui/system';
import PersonIcon from '@mui/icons-material/Person';
import EditIcon from '@mui/icons-material/Edit';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from '@mui/icons-material/Close';

const pulse = keyframes`
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
`;

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 4, backgroundColor: '#121212', minHeight: '100vh', color: 'white' }}>
          <Typography color="error">Something went wrong: {this.state.error?.message}</Typography>
        </Box>
      );
    }
    return this.props.children;
  }
}

// Add global error handler
if (typeof window !== 'undefined') {
  window.onerror = function(message, source, lineno, colno, error) {
    console.log('Global error caught:', { message, source, lineno, colno, error });
    alert(`Error: ${message}`);
    return false;
  };
}

const ActivityBox = ({ activity, onClick }) => (
  <Paper
    elevation={3}
    sx={{
      p: 1.5,
      height: '80px',
      borderRadius: '8px',
      backgroundColor: activity.completed ? '#2ecc71' : '#2980b9',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'all 0.2s ease',
      border: '2px solid rgba(255, 255, 255, 0.1)',
      '&:hover': {
        transform: 'scale(1.02)',
        backgroundColor: activity.completed ? '#27ae60' : '#2471a3',
        boxShadow: '0 0 20px rgba(41, 128, 185, 0.4)',
        border: '2px solid rgba(255, 255, 255, 0.2)',
      },
    }}
    onClick={onClick}
  >
    <Typography
      sx={{
        color: '#fff',
        textAlign: 'center',
        fontSize: '0.95rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '1px',
        textShadow: '1px 1px 2px rgba(0,0,0,0.3)',
      }}
    >
      {activity.name}
    </Typography>
  </Paper>
);

export default function Dashboard() {
  const [todaysActivities, setTodaysActivities] = useState([null, null, null]);
  const [bookmarkedActivities, setBookmarkedActivities] = useState({
    'Mind + Body': [],
    'Growth + Creation': [],
    'Purpose + People': []
  });
  const [loading, setLoading] = useState(true);
  const [xp, setXp] = useState(0);
  const [level, setLevel] = useState(1);
  const [streak, setStreak] = useState(1);
  const [message, setMessage] = useState('');
  const [username, setUsername] = useState('');
  const navigate = useNavigate();

  // Move fetchData outside useEffect so it can be reused
  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };

      // Fetch activities, user stats, and profile data
      try {
        const [activitiesResponse, userResponse, profileResponse] = await Promise.all([
          fetch('http://localhost:5001/api/tracking/all-activities', { headers }),
          fetch('http://localhost:5001/api/tracking/user-stats', { headers }),
          fetch('http://localhost:5001/api/auth/profile', { headers })
        ]);

        if (!activitiesResponse.ok) {
          throw new Error(`Activities fetch failed: ${activitiesResponse.status}`);
        }
        const activitiesData = await activitiesResponse.json();
        
        // Process activities by category
        const processedActivities = {};
        Object.entries(activitiesData.categorized_activities || {}).forEach(([category, activities]) => {
          // Keep all activities that are either active or completed today
          processedActivities[category] = activities.filter(activity => 
            activity.is_active || activity.completed_today
          );
        });
        
        setBookmarkedActivities(processedActivities);
        
        if (userResponse.ok) {
          const userData = await userResponse.json();
          setXp(userData.current_xp || 0);
          setLevel(userData.level || 1);
          setStreak(userData.streak_days || 0);
        } else {
          throw new Error(`User stats fetch failed: ${userResponse.status}`);
        }

        if (profileResponse.ok) {
          const profileData = await profileResponse.json();
          setUsername(profileData.username || '');
        }
      } catch (error) {
        console.error('Error fetching data:', error);
        setMessage('Error loading data. Please try again.');
      }
    } catch (error) {
      console.error('Error in fetchData:', error);
      setMessage('Error loading data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [navigate]);

  // Calculate XP needed for a single level
  const calculateXpForLevel = (level) => {
    return Math.round(500 + Math.pow(level, 1.5));
  };

  // Determine current level based on total XP
  const calculateCurrentLevel = (totalXp) => {
    let currentLevel = 1;
    let xpThreshold = 0;
    
    while (true) {
      const nextThreshold = xpThreshold + calculateXpForLevel(currentLevel);
      if (nextThreshold > totalXp) {
        break;
      }
      xpThreshold = nextThreshold;
      currentLevel++;
    }
    
    return {
      level: currentLevel,
      xpToCurrentLevel: xpThreshold,
      xpToNextLevel: xpThreshold + calculateXpForLevel(currentLevel)
    };
  };

  const calculateXPProgress = (totalXp) => {
    // Calculate level and thresholds based on total XP
    const { xpToCurrentLevel, xpToNextLevel } = calculateCurrentLevel(totalXp);
    
    // Calculate XP within current level
    const xpInCurrentLevel = totalXp - xpToCurrentLevel;
    const xpNeededForLevel = xpToNextLevel - xpToCurrentLevel;
    
    // Calculate percentage (ensure it's between 0 and 100)
    const percentage = (xpInCurrentLevel / xpNeededForLevel) * 100;
    return Math.min(Math.max(percentage, 0), 100);
  };

  const formatXP = (totalXp) => {
    // Calculate level and thresholds based on total XP
    const { xpToCurrentLevel, xpToNextLevel } = calculateCurrentLevel(totalXp);
    
    // Calculate XP within current level
    const xpInCurrentLevel = totalXp - xpToCurrentLevel;
    const xpNeededForLevel = xpToNextLevel - xpToCurrentLevel;
    
    // Format display (ensure non-negative numbers)
    return `${Math.max(Math.floor(xpInCurrentLevel), 0)} / ${Math.floor(xpNeededForLevel)} XP`;
  };

  // XP System Constants
  const BASE_XP = 500;
  const XP_PER_LEVEL = 1000;

  // Format date using native JavaScript
  const formatDate = () => {
    const date = new Date();
    const options = { weekday: 'long', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options).toUpperCase();
  };

  const handleActivityClick = async (activity) => {
    const selectedCount = todaysActivities.filter(Boolean).length;
    const isSelected = todaysActivities.some(a => a?.id === activity.id);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      // Toggle the activity selection in the backend
      const response = await fetch(`http://localhost:5001/api/tracking/activities/${activity.id}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ is_completion: false })
      });

      if (!response.ok) {
        throw new Error('Failed to toggle activity');
      }

      // Update local state
      if (isSelected) {
        // Remove activity if already selected
        setTodaysActivities(prev => prev.map(a => a?.id === activity.id ? null : a));
      } else if (selectedCount < 3) {
        // Add activity to first empty slot if less than 3 selected
        const firstEmpty = todaysActivities.findIndex(a => !a);
        if (firstEmpty !== -1) {
          setTodaysActivities(prev => {
            const newSelected = [...prev];
            newSelected[firstEmpty] = activity;
            return newSelected;
          });
        }
      }
    } catch (error) {
      console.error('Error toggling activity:', error);
      setMessage("Error updating activity selection. Please try again.");
    }
  };

  const animateXPGain = (startXP, endXP, newLevel, newStreak, xpGained, multiplier) => {
    let startTime = null;
    const duration = 1500; // 1.5 seconds animation

    const animate = (currentTime) => {
      if (!startTime) startTime = currentTime;
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const currentXP = startXP + (endXP - startXP) * progress;
      setXp(currentXP);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setXp(endXP);
        setLevel(newLevel);
        setStreak(newStreak);
        setMessage(`✅ You earned ${xpGained} XP with a ${multiplier}x multiplier!`);
        setTodaysActivities([null, null, null]);
      }
    };

    requestAnimationFrame(animate);
  };

  const handleSubmitActivities = async () => {
    try {
      const token = localStorage.getItem('token');
      const completedActivities = todaysActivities.filter(Boolean);
      
      if (completedActivities.length !== 3) {
        setMessage("Please select exactly 3 activities to complete.");
        return;
      }

      setMessage("Submitting activities...");

      // Submit activities one by one
      let totalXpGained = 0;
      let newLevel = level;
      let newStreak = streak;
      let submissionSuccessful = true;

      for (const activity of completedActivities) {
        try {
          const response = await fetch(`http://localhost:5001/api/tracking/activities/${activity.id}/toggle?complete=true`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            }
          });

          if (!response.ok) {
            throw new Error(`Failed to submit activity ${activity.name}`);
          }

          const data = await response.json();
          
          // Defensive defaults for all values
          totalXpGained = Number(data.totalXpGained) || 0;
          newLevel = Number(data.level) || 1;
          newStreak = Number(data.streak) || 0;
          
          // Log the response to debug
          console.log(`Activity ${activity.name} response:`, data);
        } catch (error) {
          console.error(`Error submitting activity ${activity.name}:`, error);
          submissionSuccessful = false;
          break;
        }
      }

      if (submissionSuccessful) {
        // Calculate new XP with defensive defaults
        const newXP = Number(xp) + Number(totalXpGained);
        
        // Animate XP gain with safe values
        if (totalXpGained > 0) {
          animateXPGain(
            Number(xp) || 0,
            newXP,
            Number(newLevel) || 1,
            Number(newStreak) || 0,
            Number(totalXpGained) || 0,
            Math.min(Number(newStreak) || 0, 4)
          );
        }

        // Clear today's activities
        setTodaysActivities([null, null, null]);
        
        // Refresh data to get updated activities and stats
        await fetchData();
        
        // Log the final state with defensive defaults
        console.log('Submission successful - Final state:', {
          xp: Number(newXP) || 0,
          level: Number(newLevel) || 1,
          streak: Number(newStreak) || 0,
          totalXpGained: Number(totalXpGained) || 0
        });
      } else {
        setMessage("Some activities failed to submit. Please try again.");
      }

    } catch (error) {
      console.error('Error submitting activities:', error);
      setMessage("Error submitting activities. Please try again.");
    }
  };

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#121212'
      }}>
        <CircularProgress sx={{ color: '#00ff00' }} />
      </Box>
    );
  }

  const handleResetProgress = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to reset your level, XP, streak, and activity progress?"
    );
  
    if (!confirmed) return;
  
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5001/api/tracking/reset-user', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
  
      if (!response.ok) {
        throw new Error('Failed to reset user progress');
      }
  
      setMessage('🧹 Progress has been reset.');
      setXp(0);
      setLevel(1);
      setStreak(0);
      setTodaysActivities([null, null, null]);
  
      // Refresh data to reflect reset
      await fetchData();
    } catch (error) {
      console.error('Error resetting user progress:', error);
      setMessage('Error resetting progress. Please try again.');
    }
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      backgroundColor: '#121212',
      backgroundImage: 'radial-gradient(circle at center, #1a1a1a 0%, #121212 100%)',
      color: 'white',
      position: 'relative',
      overflow: 'hidden',
      pt: 4
    }}>
      {/* Username Display */}
      <Box sx={{
        position: 'absolute',
        top: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        alignItems: 'center',
        gap: 1
      }}>
        <PersonIcon sx={{ color: '#00ff00' }} />
        <Typography sx={{
          color: '#00ff00',
          fontSize: '1.2rem',
          fontFamily: 'Impact, sans-serif',
          textTransform: 'uppercase',
          letterSpacing: '1px'
        }}>
          {username}
        </Typography>
      </Box>

      {/* Date and Streak Display */}
      <Box sx={{
        position: 'absolute',
        top: 20,
        left: 20,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: 1
      }}>
        <Typography sx={{
          color: '#00ff00',
          fontSize: '1.5rem',
          fontFamily: 'Impact, sans-serif',
          textShadow: '0 0 10px rgba(0, 255, 0, 0.5)'
        }}>
          {formatDate()}
        </Typography>
        <Typography sx={{
          color: '#00ff00',
          fontSize: '1rem',
          fontFamily: 'monospace',
          opacity: 0.8
        }}>
          🔥 Streak Multiplier: {Math.min(streak, 4)}x
        </Typography>
      </Box>

      {/* Single XP Progress Bar */}
      <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto', px: 3, mt: 8, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography sx={{ color: '#00ff00', fontWeight: 'bold' }}>
            LEVEL {level}
          </Typography>
          <Typography sx={{ color: '#00ff00', fontWeight: 'bold' }}>
            LEVEL {level + 1}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={calculateXPProgress(xp)}
          sx={{
            height: 20,
            borderRadius: 10,
            backgroundColor: '#1a1a1a',
            border: '2px solid #00ff00',
            '& .MuiLinearProgress-bar': {
              backgroundColor: '#00ff00',
            }
          }}
        />
        <Typography sx={{ color: '#00ff00', textAlign: 'center', mt: 1 }}>
          {formatXP(xp)}
        </Typography>
      </Box>

      {/* Message Display */}
      {message && (
        <Typography sx={{
          textAlign: 'center',
          color: '#00ff00',
          mb: 2,
          fontSize: '1.1rem',
          fontFamily: 'Impact, sans-serif',
          animation: `${pulse} 1s`
        }}>
          {message}
        </Typography>
      )}

      {/* Today's Activities Section */}
      <Box sx={{ 
        maxWidth: '600px', 
        mx: 'auto', 
        px: 3,
        mb: 4
      }}>
        <Typography sx={{
          color: '#00ff00',
          fontSize: '1.2rem',
          mb: 2,
          textAlign: 'center',
          fontFamily: 'Impact, sans-serif'
        }}>
          TODAY'S ACTIVITIES ({todaysActivities.filter(Boolean).length}/3)
        </Typography>
        
        <Stack direction="row" spacing={2} justifyContent="center">
          {[0, 1, 2].map((index) => (
            <Box key={index} sx={{ flex: 1, maxWidth: 200 }}>
              {todaysActivities[index] ? (
                <Paper sx={{
                  p: 2,
                  backgroundColor: 'rgba(0, 255, 0, 0.1)',
                  border: '2px solid #00ff00',
                  borderRadius: '10px',
                  position: 'relative',
                  height: '100px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center'
                }}>
                  <IconButton
                    size="small"
                    sx={{
                      position: 'absolute',
                      top: 5,
                      right: 5,
                      color: 'rgba(255, 255, 255, 0.7)'
                    }}
                    onClick={() => handleActivityClick(todaysActivities[index])}
                  >
                    <CloseIcon />
                  </IconButton>
                  <Typography sx={{ color: '#00ff00', textAlign: 'center' }}>
                    {todaysActivities[index].name}
                  </Typography>
                </Paper>
              ) : (
                <Paper sx={{
                  p: 2,
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '2px dashed rgba(0, 255, 0, 0.3)',
                  borderRadius: '10px',
                  height: '100px',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center'
                }}>
                  <Typography sx={{ color: 'rgba(0, 255, 0, 0.5)' }}>
                    Select Below
                  </Typography>
                </Paper>
              )}
            </Box>
          ))}
        </Stack>

        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Button
            variant="contained"
            disabled={todaysActivities.filter(Boolean).length !== 3}
            onClick={handleSubmitActivities}
            sx={{
              backgroundColor: '#00ff00',
              color: '#000',
              '&:hover': {
                backgroundColor: '#00cc00'
              },
              '&:disabled': {
                backgroundColor: 'rgba(0, 255, 0, 0.3)',
                color: 'rgba(0, 0, 0, 0.3)'
              }
            }}
          >
            Submit Activities
          </Button>
        </Box>
      </Box>

      {/* Your Selected Activities Section */}
      <Box sx={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 4,
        p: 4,
        mt: 4
      }}>
        {Object.entries(bookmarkedActivities).map(([category, categoryActivities]) => (
          <Box key={category} sx={{ 
            textAlign: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.4)',
            borderRadius: '15px',
            p: 3,
            border: '1px solid rgba(0, 255, 0, 0.1)'
          }}>
            <Typography sx={{
              color: '#00ff00',
              fontSize: '1.5rem',
              fontFamily: 'Impact, sans-serif',
              mb: 3,
              textTransform: 'uppercase',
              textShadow: '0 0 10px rgba(0, 255, 0, 0.5)'
            }}>
              {category}
            </Typography>
            <Stack spacing={2}>
              {categoryActivities.map((activity) => (
                <Card key={activity.id} sx={{
                  backgroundColor: 'rgba(0, 0, 0, 0.6)',
                  border: '2px solid',
                  borderColor: todaysActivities.some(a => a?.id === activity.id) ? '#00ff00' : 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '10px',
                  p: 2,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 5px 15px rgba(0, 255, 0, 0.3)',
                    borderColor: '#00ff00'
                  }
                }} onClick={() => handleActivityClick(activity)}>
                  <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <Typography sx={{
                      color: todaysActivities.some(a => a?.id === activity.id) ? '#00ff00' : 'white',
                      fontFamily: 'Helvetica, Arial, sans-serif',
                      fontWeight: 'bold'
                    }}>
                      {activity.name}
                    </Typography>
                    {todaysActivities.some(a => a?.id === activity.id) && (
                      <CheckCircleIcon sx={{ color: '#00ff00' }} />
                    )}
                  </Box>
                </Card>
              ))}
            </Stack>
          </Box>
        ))}
      </Box>

      {/* Edit Activities Button */}
      <Button
        variant="contained"
        startIcon={<EditIcon />}
        onClick={() => navigate('/activities')}
        sx={{
          position: 'absolute',
          top: 20,
          right: 20,
          backgroundColor: '#00ff00',
          color: 'black',
          fontFamily: 'Impact, sans-serif',
          '&:hover': {
            backgroundColor: '#00cc00'
          }
        }}
      >
        EDIT ACTIVITIES
      </Button>
      <Button
  variant="outlined"
  onClick={handleResetProgress}
  sx={{
    position: 'absolute',
    top: 70,
    right: 20,
    borderColor: '#ff4d4d',
    color: '#ff4d4d',
    fontFamily: 'Impact, sans-serif',
    '&:hover': {
      backgroundColor: '#ff4d4d',
      color: 'black'
    }
  }}
>
  RESET PROGRESS
</Button>

    </Box>
  );
} 