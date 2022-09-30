import React from 'react';
import pooh from './assets/images/pooh.gif';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={pooh} alt="pooh" />
        <p>
            🤫404 Not Found😴
        </p>
        <span className="App-notify">
            In progress...
        </span>
      </header>
    </div>
  );
}

export default App;
