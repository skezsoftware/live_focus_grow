import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Chip,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Fade,
  IconButton,
  CircularProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import { keyframes } from '@mui/system';
import { useNavigate } from 'react-router-dom';

const pulse = keyframes`
  0% {
    transform: scale(1);
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 30px rgba(0, 255, 0, 0.7);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
  }
`;

const glowText = keyframes`
  0% {
    text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00, 0 0 30px #00ff00;
  }
  50% {
    text-shadow: 0 0 15px #00ff00, 0 0 25px #00ff00, 0 0 35px #00ff00;
  }
  100% {
    text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00, 0 0 30px #00ff00;
  }
`;

export default function ActivitySetup() {
  const [activities, setActivities] = useState({
    'Mind + Body': [],
    'Growth + Creation': [],
    'Purpose + People': []
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [newActivity, setNewActivity] = useState({ name: '', category: 'Mind + Body' });
  const [selectionCounts, setSelectionCounts] = useState({
    "Mind + Body": 0,
    "Growth + Creation": 0,
    "Purpose + People": 0
  });
  const navigate = useNavigate();

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch('http://localhost:5001/api/tracking/all-activities', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch activities');
        }

        const data = await response.json();
        console.log('Fetched activities:', data);

        // Process activities and update selection counts
        if (data.categorized_activities) {
          const processedActivities = {};
          const initialCounts = {
            "Mind + Body": 0,
            "Growth + Creation": 0,
            "Purpose + People": 0
          };

          // Process activities and count selected ones
          Object.entries(data.categorized_activities).forEach(([category, activities]) => {
            processedActivities[category] = activities.map(activity => ({
              ...activity,
              selected: activity.is_active || activity.completed_today // Consider both active and completed activities as selected
            }));
            initialCounts[category] = activities.filter(a => a.is_active || a.completed_today).length;
          });

          setActivities(processedActivities);
          setSelectionCounts(initialCounts);
        }

        setLoading(false);
      } catch (error) {
        console.error('Error fetching activities:', error);
        setMessage('Error loading activities. Please try refreshing the page.');
        setLoading(false);
      }
    };

    fetchActivities();
  }, [navigate]);

  const handleActivitySelect = async (category, activity) => {
    try {
      // Check if the activity is already selected
      const isSelected = activity.selected || activity.is_active || activity.completed_today;
      const newIsSelected = !isSelected;
      
      // Count currently selected activities in this category (including completed ones)
      const currentSelectedCount = activities[category].filter(a => 
        (a.selected || a.is_active || a.completed_today) && a.id !== activity.id
      ).length;

      // If trying to select and already at limit
      if (newIsSelected && currentSelectedCount >= 5) {
        setMessage(`You can only select 5 activities per category. You've reached the limit for ${category}.`);
        return;
      }

      // Update backend first
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5001/api/tracking/activities/${activity.id}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          is_completion: false,
          is_active: newIsSelected
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update activity selection');
      }

      const data = await response.json();
      
      // Update activities list to reflect selection
      setActivities(prev => ({
        ...prev,
        [category]: prev[category].map(a => 
          a.id === activity.id 
            ? { ...a, selected: newIsSelected, is_active: data.is_active }
            : a
        )
      }));

      // Update selection counts based on all relevant states
      const newCount = activities[category].filter(a => 
        (a.id === activity.id ? newIsSelected : (a.selected || a.is_active || a.completed_today))
      ).length;

      setSelectionCounts(prev => ({
        ...prev,
        [category]: newCount
      }));

      // Show success message
      setMessage(data.message || `${activity.name} ${newIsSelected ? 'selected' : 'deselected'}`);

    } catch (error) {
      console.error('Error updating activity selection:', error);
      setMessage('Failed to update activity selection. Please try again.');
    }
  };

  const handleAddCustomActivity = async (category) => {
    const activityName = prompt(`Add Custom Activity to ${category}:`);
    if (!activityName) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5001/api/tracking/custom-activities', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          name: activityName,
          category: category,
          type: 'custom'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create custom activity');
      }

      // Refresh activities list
      const updatedResponse = await fetch('http://localhost:5001/api/tracking/all-activities', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      if (!updatedResponse.ok) {
        throw new Error('Failed to refresh activities');
      }

      const data = await updatedResponse.json();
      
      if (data.categorized_activities) {
        const processedActivities = {};
        const initialCounts = {
          "Mind + Body": 0,
          "Growth + Creation": 0,
          "Purpose + People": 0
        };

        // Process activities and count selected ones
        Object.entries(data.categorized_activities).forEach(([category, activities]) => {
          processedActivities[category] = activities.map(activity => ({
            ...activity,
            selected: activity.is_active
          }));
          initialCounts[category] = activities.filter(a => a.is_active).length;
        });

        setActivities(processedActivities);
        setSelectionCounts(initialCounts);
      }

      setMessage(`Added new activity: ${activityName}`);
    } catch (error) {
      console.error('Error adding custom activity:', error);
      setMessage('Failed to add custom activity. Please try again.');
    }
  };

  const handleDeleteActivity = async (activity, e) => {
    e.stopPropagation(); // Prevent activity selection when clicking delete

    if (!activity.is_custom) {
      setMessage("Cannot delete default activities");
      return;
    }

    const confirmed = window.confirm(`Are you sure you want to delete "${activity.name}"?`);
    if (!confirmed) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5001/api/tracking/custom-activities/${activity.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete activity');
      }

      // If the activity was selected, update the selection count
      if (activity.selected) {
        setSelectionCounts(prev => ({
          ...prev,
          [activity.category]: prev[activity.category] - 1
        }));
      }

      // Remove the activity from the state
      setActivities(prev => ({
        ...prev,
        [activity.category]: prev[activity.category].filter(a => a.id !== activity.id)
      }));

      setMessage(`Deleted activity: ${activity.name}`);
    } catch (error) {
      console.error('Error deleting activity:', error);
      setMessage('Failed to delete activity. Please try again.');
    }
  };

  const handleSaveActivities = async () => {
    // Check if each category has exactly 5 selections
    const isValid = Object.values(selectionCounts).every(count => count === 5);
    if (!isValid) {
      setMessage('Please select exactly 5 activities in each category');
      return;
    }

    try {
      // Get IDs of all selected activities (including completed ones)
      const selectedActivityIds = Object.values(activities)
        .flatMap(acts => acts.filter(a => a.selected || a.is_active || a.completed_today))
        .map(a => a.id);

      // Ensure we don't exceed 5 activities per category
      const categoryCounts = {};
      const finalSelectedIds = selectedActivityIds.filter(id => {
        const activity = Object.values(activities)
          .flatMap(acts => acts)
          .find(a => a.id === id);
        
        if (!activity) return false;
        
        categoryCounts[activity.category] = (categoryCounts[activity.category] || 0) + 1;
        return categoryCounts[activity.category] <= 5;
      });

      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5001/api/tracking/activities', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          selected_activities: finalSelectedIds
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save activities');
      }

      // Navigate to dashboard on success
      navigate('/dashboard');
    } catch (error) {
      console.error('Error saving activities:', error);
      setMessage(error.message || 'Failed to save activities. Please try again.');
    }
  };

  const SelectionCounter = ({ category }) => (
    <Typography sx={{
      color: selectionCounts[category] === 5 ? '#00ff00' : 'white',
      fontSize: '1rem',
      fontFamily: 'Impact, sans-serif',
    }}>
      {selectionCounts[category]}/5 SELECTED
    </Typography>
  );

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

  return (
    <Box sx={{ 
      p: { xs: 2, sm: 3, md: 4 }, 
      maxWidth: '100%', 
      minHeight: '100vh',
      backgroundColor: '#121212',
      color: 'white',
      position: 'relative',
      pb: { xs: 20, sm: 24, md: 28 }, // Increased bottom padding significantly
      display: 'flex',
      flexDirection: 'column',
      overflow: 'auto',
    }}>
      {/* Message Display */}
      {message && (
        <Typography sx={{
          textAlign: 'center',
          color: '#00ff00',
          animation: `${pulse} 1s`,
          fontSize: { xs: '0.9rem', sm: '1rem' },
          mt: { xs: 2, sm: 3 }
        }}>
          {message}
        </Typography>
      )}

      <Typography 
        variant="h3" 
        sx={{ 
          textAlign: 'center',
          fontSize: { xs: '2rem', sm: '2.5rem', md: '3.5rem' },
          fontWeight: '700',
          fontFamily: 'Impact, sans-serif',
          color: '#ffffff',
          textTransform: 'uppercase',
          animation: `${glowText} 3s infinite`,
          letterSpacing: '2px',
          mt: { xs: 4, sm: 2 },
        }}
      >
        Select Your Missions
      </Typography>

      <Typography sx={{ 
        textAlign: 'center', 
        color: '#00ff00',
        fontSize: { xs: '1rem', sm: '1.1rem', md: '1.2rem' },
        textShadow: '0 0 5px #00ff00',
        fontFamily: 'Helvetica, Arial, sans-serif',
        px: 2,
        mb: { xs: 1, sm: 2 },
      }}>
        Choose 5 activities from each category to display on your dashboard.
      </Typography>

      {/* Category Selection Summary */}
      <Box sx={{
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'center',
        gap: { xs: 2, sm: 4 },
        mb: { xs: 3, sm: 4 },
      }}>
        {Object.entries(selectionCounts).map(([category, count]) => (
          <Typography
            key={category}
            sx={{
              color: count === 5 ? '#00ff00' : '#fff',
              fontFamily: 'Impact, sans-serif',
              fontSize: { xs: '1.1rem', sm: '1.2rem', md: '1.3rem' },
              textShadow: count === 5 ? '0 0 10px #00ff00' : 'none',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              textAlign: 'center',
            }}
          >
            {category.split(' + ')[0]}: {count}/5
          </Typography>
        ))}
      </Box>

      {/* Activities Grid */}
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: { xs: 4, sm: 6, md: 8 },
      }}>
        {Object.entries(activities).map(([category, categoryActivities]) => (
          <Box key={category} sx={{
            background: 'linear-gradient(45deg, rgba(0,0,0,0.9) 0%, rgba(20,20,20,0.9) 100%)',
            borderRadius: '15px',
            p: { xs: 2, sm: 3, md: 4 },
            border: '1px solid rgba(0, 255, 0, 0.1)',
            boxShadow: '0 0 20px rgba(0, 255, 0, 0.1)',
          }}>
            {/* Category Header */}
            <Box sx={{ 
              display: 'flex', 
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between', 
              alignItems: { xs: 'flex-start', sm: 'center' },
              gap: { xs: 2, sm: 0 },
              mb: { xs: 2, sm: 3, md: 4 },
            }}>
              <Typography variant="h4" sx={{ 
                fontWeight: '700',
                fontSize: { xs: '1.5rem', sm: '1.8rem', md: '2.2rem' },
                color: '#00ff00',
                textTransform: 'uppercase',
                fontFamily: 'Impact, sans-serif',
                textShadow: '0 0 10px rgba(0, 255, 0, 0.5)',
              }}>
                {category}
              </Typography>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 2,
                width: { xs: '100%', sm: 'auto' },
                justifyContent: { xs: 'space-between', sm: 'flex-end' },
              }}>
                <Typography sx={{
                  color: selectionCounts[category] === 5 ? '#00ff00' : selectionCounts[category] > 5 ? '#ff0000' : '#fff',
                  fontFamily: 'Impact, sans-serif',
                  fontSize: { xs: '1rem', sm: '1.1rem', md: '1.2rem' },
                  textShadow: selectionCounts[category] === 5 
                    ? '0 0 10px #00ff00' 
                    : selectionCounts[category] > 5 
                      ? '0 0 10px #ff0000'
                      : 'none',
                }}>
                  {selectionCounts[category]}/5 SELECTED
                  {selectionCounts[category] > 5 && (
                    <Typography component="span" sx={{ 
                      color: '#ff0000',
                      fontSize: '0.8em',
                      display: 'block',
                      mt: 0.5
                    }}>
                      TOO MANY SELECTED
                    </Typography>
                  )}
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => handleAddCustomActivity(category)}
                  sx={{
                    color: '#00ff00',
                    borderColor: '#00ff00',
                    backgroundColor: 'transparent',
                    fontSize: { xs: '0.8rem', sm: '0.9rem' },
                    whiteSpace: 'nowrap',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 255, 0, 0.1)',
                      borderColor: '#00ff00'
                    }
                  }}
                >
                  ADD CUSTOM
                </Button>
              </Box>
            </Box>
            
            {/* Activities Grid */}
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(3, 1fr)',
                lg: 'repeat(4, 1fr)'
              },
              gap: { xs: 1.5, sm: 2 }
            }}>
              {categoryActivities.map((activity) => (
                <Box
                  key={activity.id}
                  onClick={() => handleActivitySelect(category, activity)}
                  sx={{
                    p: { xs: 2, sm: 3 },
                    borderRadius: '10px',
                    cursor: 'pointer',
                    border: '1px solid',
                    borderColor: activity.selected ? '#00ff00' : 'rgba(0, 255, 0, 0.3)',
                    backgroundColor: activity.selected ? 'rgba(0, 255, 0, 0.1)' : 'transparent',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    position: 'relative',
                    minHeight: { xs: '50px', sm: '60px' },
                    '&:hover': {
                      backgroundColor: activity.selected ? 'rgba(0, 255, 0, 0.15)' : 'rgba(0, 255, 0, 0.05)',
                      borderColor: '#00ff00',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 12px rgba(0, 255, 0, 0.2)'
                    }
                  }}
                >
                  <Typography sx={{ 
                    color: activity.selected ? '#00ff00' : 'white',
                    fontWeight: activity.selected ? 600 : 400,
                    flex: 1,
                    mr: activity.is_custom ? 2 : 0,
                    fontSize: { xs: '0.9rem', sm: '1rem' },
                  }}>
                    {activity.name}
                  </Typography>
                  {activity.is_custom && (
                    <IconButton
                      size="small"
                      onClick={(e) => handleDeleteActivity(activity, e)}
                      sx={{
                        color: 'rgba(255, 0, 0, 0.7)',
                        backgroundColor: 'rgba(0, 0, 0, 0.2)',
                        padding: '4px',
                        '&:hover': {
                          color: 'red',
                          backgroundColor: 'rgba(255, 0, 0, 0.1)'
                        }
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  )}
                </Box>
              ))}
            </Box>
          </Box>
        ))}
      </Box>

      {/* Save Button */}
      <Box sx={{ 
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
        borderTop: '1px solid #00ff00',
        p: { xs: 2, sm: 3 },
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'flex-end', // Changed to flex-end since we moved the counts
        alignItems: 'center',
        gap: { xs: 2, sm: 0 },
        zIndex: 1000,
        backdropFilter: 'blur(5px)',
      }}>
        <Button
          variant="contained"
          onClick={handleSaveActivities}
          disabled={!Object.values(selectionCounts).every(count => count === 5)}
          sx={{
            backgroundColor: '#00ff00',
            color: '#000',
            padding: { xs: '8px 24px', sm: '12px 48px' },
            fontSize: { xs: '1rem', sm: '1.2rem' },
            fontFamily: 'Impact, sans-serif',
            width: { xs: '100%', sm: 'auto' },
            whiteSpace: 'nowrap',
            '&:hover': {
              backgroundColor: '#00cc00'
            },
            '&:disabled': {
              backgroundColor: 'rgba(0, 255, 0, 0.3)',
              color: 'rgba(0, 0, 0, 0.3)'
            }
          }}
        >
          SAVE AND CONTINUE TO DASHBOARD
        </Button>
      </Box>

      <Dialog 
        open={openDialog} 
        onClose={() => setOpenDialog(false)}
        PaperProps={{
          sx: {
            backgroundColor: '#121212',
            color: 'white',
            border: '1px solid #00ff00',
            boxShadow: '0 0 20px rgba(0, 255, 0, 0.3)',
          }
        }}
      >
        <DialogTitle sx={{ 
          fontFamily: 'Impact, sans-serif',
          color: '#00ff00',
          textTransform: 'uppercase',
        }}>
          Create Custom Mission
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
            <InputLabel sx={{ color: '#00ff00' }}>Category</InputLabel>
            <Select
              value={newActivity.category}
              label="Category"
              onChange={(e) => setNewActivity(prev => ({ ...prev, category: e.target.value }))}
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(0, 255, 0, 0.5)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00ff00',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00ff00',
                },
              }}
            >
              {Object.keys(activities).map((category) => (
                <MenuItem key={category} value={category}>
                  {category}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            autoFocus
            margin="dense"
            label="Mission Name"
            fullWidth
            value={newActivity.name}
            onChange={(e) => setNewActivity(prev => ({ ...prev, name: e.target.value }))}
            sx={{
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
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button 
            onClick={() => setOpenDialog(false)}
            sx={{ 
              color: '#00ff00',
              '&:hover': {
                backgroundColor: 'rgba(0, 255, 0, 0.1)',
              }
            }}
          >
            CANCEL
          </Button>
          <Button 
            onClick={() => handleAddCustomActivity(newActivity.category)} 
            variant="contained"
            sx={{ 
              backgroundColor: '#00ff00',
              color: '#000000',
              '&:hover': {
                backgroundColor: '#00cc00',
              }
            }}
          >
            ADD MISSION
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 