const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({ message: 'Reflexia API funcionant!' });
});

app.listen(PORT, () => {
  console.log(`Servidor escoltant al port ${PORT}`);
});

const pool = require('./db');

app.get('/test-db', async (req, res) => {
  const result = await pool.query('SELECT * FROM Usuari');
  res.json(result.rows);
});