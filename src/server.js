const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const session = require('express-session');
const passport = require('passport');
const LocalStrategy = require('passport-local').Strategy;
const path = require('path');
const expressLayouts = require('express-ejs-layouts');
const cookieParser = require('cookie-parser');
const csrf = require('csurf');
const flash = require('connect-flash');
const config = require('./config');
const { sequelize, User, Game, Question, Player, Answer } = require('./models');
const { router: authRouter, isAuthenticated } = require('./routes/auth');

const app = express();
const httpServer = createServer(app);

// Basic middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser(config.app.secretKey));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Session store
const SequelizeStore = require('connect-session-sequelize')(session.Store);
const sessionStore = new SequelizeStore({
    db: sequelize,
    tableName: 'sessions'
});

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(expressLayouts);
app.set('layout', path.join(__dirname, 'views/layouts/base'));

// Session middleware
const sessionMiddleware = session({
    secret: config.app.secretKey,
    store: sessionStore,
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: false,
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000, // 24 hours
        sameSite: 'lax'
    }
});

// Create session table
sessionStore.sync();

// Initialize Socket.IO with session sharing
const io = new Server(httpServer, {
    cors: {
        origin: true,
        methods: ['GET', 'POST'],
        credentials: true,
        cookie: {
            httpOnly: true,
            sameSite: 'lax'
        }
    },
    allowEIO3: true,
    transports: ['websocket']
});

// Share session middleware with Socket.IO
const wrap = middleware => (socket, next) => middleware(socket.request, {}, next);

// Socket.IO middleware
io.use(wrap(sessionMiddleware));
io.use(wrap(passport.initialize()));
io.use(wrap(passport.session()));
io.use((socket, next) => {
    // Save session data for Socket.IO
    const session = socket.request.session;
    if (session) {
        session.save((err) => {
            if (err) {
                console.error('Error saving session:', err);
                return next(err);
            }
            next();
        });
    } else {
        next();
    }
});

app.use(sessionMiddleware);

// Authentication middleware
app.use(passport.initialize());
app.use(passport.session());
app.use(flash());

// CSRF protection
app.use(csrf({ cookie: true }));

// Template locals middleware
app.use((req, res, next) => {
  res.locals.csrfToken = req.csrfToken();
  res.locals.user = req.user;
  res.locals.error = req.flash('error');
  res.locals.success = req.flash('success');
  next();
});

// Passport configuration
passport.use(new LocalStrategy(
  async (username, password, done) => {
    try {
      const user = await User.findOne({ where: { username } });
      if (!user) {
        return done(null, false, { message: 'Incorrect username.' });
      }
      const isValid = await user.checkPassword(password);
      if (!isValid) {
        return done(null, false, { message: 'Incorrect password.' });
      }
      return done(null, user);
    } catch (err) {
      return done(err);
    }
  }
));

passport.serializeUser((user, done) => {
  done(null, user.id);
});

passport.deserializeUser(async (id, done) => {
  try {
    const user = await User.findByPk(id);
    done(null, user);
  } catch (err) {
    done(err);
  }
});

// Socket.IO state
const activeConnections = new Map();
const roomParticipants = new Map();

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);
  activeConnections.set(socket.id, { connectedAt: Date.now() });

  // Join game room
  socket.on('player_join', async (data) => {
    try {
      const game = await Game.findOne({ where: { pin: data.pin } });
      if (!game) {
        socket.emit('join_error', { message: 'Game not found' });
        return;
      }

      // Handle host connection
      if (data.is_host) {
        if (!data.host_id || game.host_id !== parseInt(data.host_id)) {
          socket.emit('join_error', { message: 'Unauthorized host' });
          return;
        }

        socket.join(data.pin);
        socket.gamePin = data.pin;
        socket.session.gamePin = data.pin;
        socket.session._user_id = data.host_id;
        await socket.session.save();
        
        if (!roomParticipants.has(data.pin)) {
          roomParticipants.set(data.pin, new Set());
        }
        roomParticipants.get(data.pin).add(socket.id);
        
        activeConnections.set(socket.id, {
          ...activeConnections.get(socket.id),
          gamePin: data.pin,
          isHost: true,
          hostId: parseInt(data.host_id)
        });
        
        return;
      }

      // Handle player connection
      const player = await Player.findByPk(data.player_id);
      if (!player) {
        socket.emit('join_error', { message: 'Player not found' });
        return;
      }

      if (player.game_id !== game.id) {
        if (data.rejoin) {
          player.game_id = game.id;
          await player.save();
        } else {
          socket.emit('join_error', { message: 'Player does not belong to this game' });
          return;
        }
      }

      socket.join(data.pin);
      socket.gamePin = data.pin;
      socket.session.gamePin = data.pin;
      socket.session.player_id = player.id;
      await socket.session.save();

      if (!roomParticipants.has(data.pin)) {
        roomParticipants.set(data.pin, new Set());
      }
      roomParticipants.get(data.pin).add(socket.id);

      const playerInfo = {
        id: player.id,
        nickname: player.nickname,
        score: player.score,
        is_ready: data.is_ready || false
      };

      activeConnections.set(socket.id, {
        ...activeConnections.get(socket.id),
        gamePin: data.pin,
        playerInfo
      });

      // Update player ready status
      if (!data.rejoin) {
        player.is_ready = true;
        await player.save();
      }

      // Get current room participants
      const participants = Array.from(roomParticipants.get(data.pin))
        .map(sid => activeConnections.get(sid)?.playerInfo)
        .filter(Boolean);

      // Notify room about participants
      io.to(data.pin).emit('room_participants_changed', {
        connected_players: participants
      });

      // Emit join success
      socket.emit('player_joined', {
        player_id: player.id,
        nickname: player.nickname,
        score: player.score,
        is_ready: player.is_ready,
        is_rejoin: data.rejoin || false
      });

      if (player.is_ready) {
        io.to(data.pin).emit('player_ready', {
          player_id: player.id,
          nickname: player.nickname
        });
      }

      // Check if all players are ready
      const allPlayers = await Player.findAll({ where: { game_id: game.id } });
      const readyPlayers = allPlayers.filter(p => p.is_ready);
      if (readyPlayers.length === allPlayers.length) {
        io.to(data.pin).emit('all_players_ready');
      }
    } catch (error) {
      console.error('Error in player_join:', error);
      socket.emit('join_error', { message: 'Failed to join game' });
    }
  });

  // Game events
  socket.on('game_started', async () => {
    try {
      const gamePin = socket.session?.gamePin;
      const hostId = socket.session?._user_id;

      if (!gamePin || !hostId) {
        socket.emit('error', { message: 'Invalid session' });
        return;
      }

      const game = await Game.findOne({ where: { pin: gamePin } });
      if (!game || game.host_id !== parseInt(hostId)) {
        socket.emit('error', { message: 'Unauthorized' });
        return;
      }

      if (!game.started_at) {
        game.started_at = new Date();
        game.current_question_index = -1;
        await game.save();
      }

      const questions = await Question.findAll({
        where: { game_id: game.id },
        order: [['id', 'ASC']]
      });

      io.to(gamePin).emit('game_started', {
        started_at: game.started_at.toISOString(),
        total_questions: questions.length,
        current_question_index: game.current_question_index,
        redirect: {
          host: `/game/host/${gamePin}`,
          player: `/game/play/${gamePin}`
        }
      });
    } catch (error) {
      console.error('Error in game_started:', error);
      socket.emit('error', { message: 'Failed to start game' });
    }
  });

  // Question events
  socket.on('preparing_next_question', async (data) => {
    try {
      const gamePin = data.pin;
      const hostId = socket.session?._user_id;

      if (!gamePin || !hostId) {
        socket.emit('error', { message: 'Invalid session' });
        return;
      }

      const game = await Game.findOne({ where: { pin: gamePin } });
      if (!game || game.host_id !== parseInt(hostId)) {
        socket.emit('error', { message: 'Unauthorized' });
        return;
      }

      const questions = await Question.findAll({
        where: { game_id: game.id },
        order: [['id', 'ASC']]
      });

      game.current_question_index += 1;
      if (game.current_question_index >= questions.length) {
        socket.emit('error', { message: 'No more questions available' });
        return;
      }

      const question = questions[game.current_question_index];
      const questionData = {
        id: question.id,
        content: question.content,
        answers: [question.correct_answer, ...question.incorrect_answers],
        time_limit: question.time_limit || 20,
        points: question.points || 1000
      };

      game.current_question_started_at = new Date();
      await game.save();

      io.to(gamePin).emit('question_preparing', {
        question: questionData,
        total_questions: questions.length,
        current_index: game.current_question_index,
        started_at: game.current_question_started_at.toISOString()
      });

      setTimeout(() => {
        io.to(gamePin).emit('question_started', questionData);
      }, 2000);
    } catch (error) {
      console.error('Error in preparing_next_question:', error);
      socket.emit('error', { message: 'Failed to prepare question' });
    }
  });

  socket.on('submit_answer', async (data) => {
    try {
      const playerId = socket.session?.player_id;
      if (!playerId) {
        socket.emit('answer_error', { message: 'Player session not found' });
        return;
      }

      const player = await Player.findByPk(playerId);
      if (!player) {
        socket.emit('answer_error', { message: 'Player not found' });
        return;
      }

      const question = await Question.findByPk(data.question_id);
      if (!question || question.game_id !== player.game_id) {
        socket.emit('answer_error', { message: 'Invalid question' });
        return;
      }

      const existingAnswer = await Answer.findOne({
        where: { player_id: player.id, question_id: question.id }
      });

      if (existingAnswer) {
        socket.emit('answer_error', { message: 'Answer already submitted' });
        return;
      }

      const responseTime = data.response_time;
      const maxTime = question.time_limit || 20;
      const timeFactor = Math.max(0, (maxTime - responseTime) / maxTime);
      const pointsEarned = Math.floor(question.points * timeFactor);

      const isCorrect = data.answer === question.correct_answer;
      const answer = await Answer.create({
        player_id: player.id,
        question_id: question.id,
        answer_text: data.answer,
        is_correct: isCorrect,
        response_time: responseTime,
        points_awarded: isCorrect ? pointsEarned : 0
      });

      if (isCorrect) {
        player.current_streak += 1;
        player.score += pointsEarned;
      } else {
        player.current_streak = 0;
      }
      await player.save();

      io.to(socket.gamePin).emit('answer_submitted', {
        player_id: player.id,
        nickname: player.nickname,
        is_correct: isCorrect,
        points_awarded: isCorrect ? pointsEarned : 0,
        new_score: player.score,
        new_streak: player.current_streak
      });

      socket.emit('answer_result', {
        is_correct: isCorrect,
        correct_answer: question.correct_answer,
        points_awarded: isCorrect ? pointsEarned : 0,
        new_score: player.score,
        new_streak: player.current_streak
      });
    } catch (error) {
      console.error('Error in submit_answer:', error);
      socket.emit('answer_error', { message: 'Failed to submit answer' });
    }
  });

  socket.on('end_question', async (data) => {
    try {
      const gamePin = data.pin;
      const hostId = socket.session?._user_id;

      if (!gamePin || !hostId) {
        socket.emit('error', { message: 'Invalid session' });
        return;
      }

      const game = await Game.findOne({ where: { pin: gamePin } });
      if (!game || game.host_id !== parseInt(hostId)) {
        socket.emit('error', { message: 'Unauthorized' });
        return;
      }

      const question = await Question.findByPk(data.question_id);
      if (!question || question.game_id !== game.id) {
        socket.emit('error', { message: 'Invalid question' });
        return;
      }

      const answers = await Answer.findAll({
        where: { question_id: question.id },
        include: [{ model: Player, attributes: ['nickname'] }]
      });

      const answerData = answers.map(answer => ({
        player_id: answer.player_id,
        nickname: answer.Player.nickname,
        is_correct: answer.is_correct,
        points_awarded: answer.points_awarded,
        response_time: answer.response_time
      }));

      io.to(gamePin).emit('question_ended', {
        question_id: question.id,
        correct_answer: question.correct_answer,
        answers: answerData
      });
    } catch (error) {
      console.error('Error in end_question:', error);
      socket.emit('error', { message: 'Failed to end question' });
    }
  });

  socket.on('request_leaderboard', async (data) => {
    try {
      const gamePin = data.pin;
      const hostId = socket.session?._user_id;

      if (!gamePin || !hostId) {
        socket.emit('error', { message: 'Invalid session' });
        return;
      }

      const game = await Game.findOne({ where: { pin: gamePin } });
      if (!game || game.host_id !== parseInt(hostId)) {
        socket.emit('error', { message: 'Unauthorized' });
        return;
      }

      const players = await Player.findAll({
        where: { game_id: game.id },
        order: [['score', 'DESC']]
      });

      const leaderboardData = players.map(player => ({
        player_id: player.id,
        nickname: player.nickname,
        score: player.score,
        streak: player.current_streak
      }));

      io.to(gamePin).emit('leaderboard_update', {
        leaderboard: leaderboardData
      });
    } catch (error) {
      console.error('Error in request_leaderboard:', error);
      socket.emit('error', { message: 'Failed to get leaderboard' });
    }
  });

  // Disconnect handling
  socket.on('disconnect', () => {
    console.log(`Client disconnected: ${socket.id}`);
    const gamePin = socket.gamePin;
    if (gamePin && roomParticipants.has(gamePin)) {
      roomParticipants.get(gamePin).delete(socket.id);
      if (roomParticipants.get(gamePin).size === 0) {
        roomParticipants.delete(gamePin);
      }
    }
    activeConnections.delete(socket.id);
  });
});

// Routes
app.use('/auth', authRouter);
app.use('/game', require('./routes/game'));
app.use('/', require('./routes/main'));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).render('error', {
    title: 'Error',
    message: 'Something went wrong!'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).render('error', {
    title: '404 Not Found',
    message: 'The page you requested could not be found.'
  });
});

// Start server
const startServer = async (retries = 0) => {
  const PORT = config.app.port + retries;
  const HOST = config.app.host;

  try {
    await sequelize.sync();
    httpServer.listen(PORT, HOST, () => {
      console.log(`Server running at http://${HOST}:${PORT}`);
    });
  } catch (err) {
    if (err.code === 'EADDRINUSE' && retries < 10) {
      console.log(`Port ${PORT} in use, trying ${PORT + 1}...`);
      await startServer(retries + 1);
    } else {
      console.error('Failed to start server:', err);
      process.exit(1);
    }
  }
};

startServer();

module.exports = app;
