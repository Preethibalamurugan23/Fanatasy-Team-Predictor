// // const venues = ['Wankhede', 'Chepauk', 'M.Chinnaswamy Stadium, Bengaluru', 'Eden Gardens', 'Rajiv Gandhi Stadium', 'Sawai Mansingh', 'PCA Stadium', 'Feroz Shah Kotla'];
// import { venues } from './venues.js';  // Adjust the path if needed
// const teams = ['CSK', 'MI', 'RCB', 'KKR', 'SRH', 'RR', 'PBKS', 'DC', 'LSG', 'GT'];
// import { teamPlayers } from './teamPlayers.js';  // Adjust the path if needed


// const teamColors = {
//   'CSK': 'CSK',
//   'MI': 'MI',
//   'RCB': 'RCB',
//   'KKR': 'KKR',
//   'SRH': 'SRH',
//   'RR': 'RR',
//   'PBKS': 'PBKS',
//   'DC': 'DC',
//   'LSG': 'LSG',
//   'GT': 'GT'
// };

// const homeTeamSelect = document.getElementById('homeTeam');
// const awayTeamSelect = document.getElementById('awayTeam');
// const venueSelect = document.getElementById('venue');
// const inningSelect = document.getElementById('inning');
// const predictBtn = document.getElementById('predictBtn');
// const fantasyTeamDiv = document.getElementById('fantasyTeam');
// const homeLogoDiv = document.getElementById('homeLogo');
// const awayLogoDiv = document.getElementById('awayLogo');

// // Populate dropdowns
// teams.forEach(team => {
//   homeTeamSelect.add(new Option(team, team));
//   awayTeamSelect.add(new Option(team, team));
// });

// venues.forEach(venue => {
//   venueSelect.add(new Option(venue, venue));
// });

// // Show logos on selection
// function updateLogos() {
//   const home = homeTeamSelect.value;
//   const away = awayTeamSelect.value;

//   homeLogoDiv.innerHTML = home ? `<img src="assets/logos/${home}.png" alt="${home} Logo">` : '<p>Home Team</p>';
//   awayLogoDiv.innerHTML = away ? `<img src="assets/logos/${away}.png" alt="${away} Logo">` : '<p>Away Team</p>';
// }

// function findPlayerTeam(playerName) {
//   for (const [team, players] of Object.entries(teamPlayers)) {
//     if (players.includes(playerName)) {
//       return team;
//     }
//   }
//   return null; // if player not found
// }

// homeTeamSelect.addEventListener('change', updateLogos);
// awayTeamSelect.addEventListener('change', updateLogos);

// // // Predict Fantasy Team
// // predictBtn.addEventListener('click', () => {
// //   fantasyTeamDiv.innerHTML = ''; // Clear previous

// //   // Example fantasy team
// //   const predictedPlayers = [
// //     'MS Dhoni', 'Virat Kohli', 'AB de Villiers', 'Suresh Raina', 'Sunil Narine',
// //     'Andre Russell', 'Rashid Khan', 'Bhuvneshwar Kumar', 'Hardik Pandya', 'Dwayne Bravo', 'Jasprit Bumrah'
// //   ];

// //   const homeTeam = homeTeamSelect.value || 'CSK'; // fallback
// //   const awayTeam = awayTeamSelect.value || 'MI';  // fallback

// //   predictedPlayers.forEach((player, index) => {
// //     const card = document.createElement('div');
// //     card.classList.add('player-card');

// //     // Captain and Vice-Captain Tag
// //     if (index === 0) {
// //       card.innerText = player + '\n(Captain)';
// //     } else if (index === 1) {
// //       card.innerText = player + '\n(Vice-Captain)';
// //     } else {
// //       card.innerText = player;
// //     }

// //     // Alternate players from home and away team
// //     if (index % 2 === 0) {
// //       card.classList.add(teamColors[homeTeam]);
// //     } else {
// //       card.classList.add(teamColors[awayTeam]);
// //     }

// //     fantasyTeamDiv.appendChild(card);
// //   });
// // });

// predictBtn.addEventListener('click', async () => {
//   fantasyTeamDiv.innerHTML = ''; // Clear previous

//   const homeTeam = homeTeamSelect.value || 'CSK'; // fallback
//   const awayTeam = awayTeamSelect.value || 'MI';  // fallback
//   const venue = venueSelect.value || 'M.Chinnaswamy Stadium, Bengaluru';  // fallback
//   const inning = parseInt(inningSelect.value) || 1; // assuming innings are 1 or 2

//   try {
//     const response = await fetch('http://192.168.208.6:8000/predict_fantasy_points/', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json'
//       },
//       body: JSON.stringify({
//         home_team: homeTeam,
//         away_team: awayTeam,
//         venue: venue,
//         inning: inning
//       })
//     });

//     if (!response.ok) {
//       throw new Error('Prediction request failed');
//     }

//     const result = await response.json();
    
//     const predictedPlayers = result.predicted_players; // Adjust depending on backend response

//     // predictedPlayers.forEach((player, index) => {
//     //   const card = document.createElement('div');
//     //   card.classList.add('player-card');

//     //   // Captain and Vice-Captain Tag
//     //   if (index === 0) {
//     //     card.innerText = player + '\n(Captain)';
//     //   } else if (index === 1) {
//     //     card.innerText = player + '\n(Vice-Captain)';
//     //   } else {
//     //     card.innerText = player;
//     //   }

//     //   if (index % 2 === 0) {
//     //     card.classList.add(teamColors[homeTeam]);
//     //   } else {
//     //     card.classList.add(teamColors[awayTeam]);
//     //   }

//     //   fantasyTeamDiv.appendChild(card);
//     // });
        
//     predictedPlayers.forEach((player, index) => {
//       const card = document.createElement('div');
//       card.classList.add('player-card');
    
//       // Captain and Vice-Captain Tag
//       if (index === 0) {
//         card.innerText = player + '\n(Captain)';
//       } else if (index === 1) {
//         card.innerText = player + '\n(Vice-Captain)';
//       } else {
//         card.innerText = player;
//       }
    
//       const playerTeam = findPlayerTeam(player);
    
//       if (playerTeam && teamColors[playerTeam]) {
//         card.classList.add(teamColors[playerTeam]);
//       } else {
//         // card.classList.add('default-team'); // fallback
//         card.classList.add(teamColors[homeTeam]); // fallback
//       }
    
//       fantasyTeamDiv.appendChild(card);
//     });
    

//   } catch (error) {
//     console.error('Error:', error);
//     fantasyTeamDiv.innerHTML = '<p>Could not fetch fantasy team. Try again later.</p>';
//   }
// });

import { venues } from './venues.js';
import { teamPlayers } from './teamPlayers.js';

const teams = ['CSK', 'MI', 'RCB', 'KKR', 'SRH', 'RR', 'PBKS', 'DC', 'LSG', 'GT'];

const teamColors = {
  'CSK': 'CSK',
  'MI': 'MI',
  'RCB': 'RCB',
  'KKR': 'KKR',
  'SRH': 'SRH',
  'RR': 'RR',
  'PBKS': 'PBKS',
  'DC': 'DC',
  'LSG': 'LSG',
  'GT': 'GT'
};

const homeTeamSelect = document.getElementById('homeTeam');
const awayTeamSelect = document.getElementById('awayTeam');
const venueSelect = document.getElementById('venue');
const inningSelect = document.getElementById('inning');
const predictBtn = document.getElementById('predictBtn');
const fantasyTeamDiv = document.getElementById('fantasyTeam');
const homeLogoDiv = document.getElementById('homeLogo');
const awayLogoDiv = document.getElementById('awayLogo');

// Populate dropdowns with team and venue options (no default selected)
teams.forEach(team => {
  homeTeamSelect.add(new Option(team, team));
  awayTeamSelect.add(new Option(team, team));
});

venues.forEach(venue => {
  venueSelect.add(new Option(venue, venue));
});

// Helper: update team logos
function updateLogos() {
  const home = homeTeamSelect.value;
  const away = awayTeamSelect.value;

  homeLogoDiv.innerHTML = home ? `<img src="assets/logos/${home}.png" alt="${home} Logo">` : '<p>Home Team</p>';
  awayLogoDiv.innerHTML = away ? `<img src="assets/logos/${away}.png" alt="${away} Logo">` : '<p>Away Team</p>';
}

// Disable selected home team in away dropdown
function updateAwayTeamOptions() {
  const selectedHome = homeTeamSelect.value;
  Array.from(awayTeamSelect.options).forEach(option => {
    option.disabled = option.value === selectedHome;
  });
}

// Optional: disable selected away team in home dropdown
function updateHomeTeamOptions() {
  const selectedAway = awayTeamSelect.value;
  Array.from(homeTeamSelect.options).forEach(option => {
    option.disabled = option.value === selectedAway;
  });
}

function findPlayerTeam(playerName) {
  for (const [team, players] of Object.entries(teamPlayers)) {
    if (players.includes(playerName)) {
      return team;
    }
  }
  return null;
}

// Event listeners
homeTeamSelect.addEventListener('change', () => {
  updateLogos();
  updateAwayTeamOptions();
});

awayTeamSelect.addEventListener('change', () => {
  updateLogos();
  updateHomeTeamOptions();
});

predictBtn.addEventListener('click', async () => {
  fantasyTeamDiv.innerHTML = '';

  // Fallback only if user didn't touch dropdown (i.e., nothing selected)
  const homeTeam = homeTeamSelect.value || 'CSK';
  const awayTeam = awayTeamSelect.value || 'MI';
  const venue = venueSelect.value || 'M.Chinnaswamy Stadium, Bengaluru';
  const inning = parseInt(inningSelect.value) || 1;

  try {
    const response = await fetch('http://192.168.208.6:8000/predict_fantasy_points/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam, venue, inning })
    });

    if (!response.ok) throw new Error('Prediction request failed');

    const result = await response.json();
    const predictedPlayers = result.predicted_players;

    predictedPlayers.forEach((player, index) => {
      const card = document.createElement('div');
      card.classList.add('player-card');

      if (index === 0) {
        card.innerText = player + '\n(Captain)';
      } else if (index === 1) {
        card.innerText = player + '\n(Vice-Captain)';
      } else {
        card.innerText = player;
      }

      const playerTeam = findPlayerTeam(player);
      if (playerTeam && teamColors[playerTeam]) {
        card.classList.add(teamColors[playerTeam]);
      } else {
        card.classList.add(teamColors[homeTeam]);
      }

      fantasyTeamDiv.appendChild(card);
    });

  } catch (error) {
    console.error('Error:', error);
    fantasyTeamDiv.innerHTML = '<p>Could not fetch fantasy team. Try again later.</p>';
  }
});
