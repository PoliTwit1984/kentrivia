const express = require('express');
const router = express.Router();
const axios = require('axios');
const { Game, Question, Player, User } = require('../models');
const { isAuthenticated } = require('./auth');
const config = require('../config');

// Game dashboard
router.get('/dashboard', isAuthenticated, async (req, res) => {
    try {
        const games = await Game.findAll({
            where: { host_id: req.user.id },
            order: [['createdAt', 'DESC']],
            include: [
                {
                    model: Question,
                    attributes: ['id']
                },
                {
                    model: Player,
                    attributes: ['id']
                },
                {
                    model: User,
                    as: 'host',
                    attributes: ['username']
                }
            ],
            order: [['createdAt', 'DESC']]
        });

        res.render('game/dashboard', {
            title: 'My Games',
            games: games.map(game => ({
                ...game.toJSON(),
                question_count: game.Questions.length,
                player_count: game.Players.length
            }))
        });
    } catch (error) {
        console.error('Error loading dashboard:', error);
        req.flash('error', 'Failed to load games');
        res.redirect('/');
    }
});

// Create game
router.get('/create', isAuthenticated, (req, res) => {
    res.render('game/create', { 
        title: 'Create Game',
        config: config
    });
});

router.post('/create', isAuthenticated, async (req, res) => {
    const { title, category, numQuestions } = req.body;
    const errors = {};

    try {
        if (!title || title.length < 3 || title.length > 64) {
            errors.title = 'Title must be between 3 and 64 characters';
        }

        if (!numQuestions || numQuestions < 5 || numQuestions > 50) {
            errors.numQuestions = 'Number of questions must be between 5 and 50';
        }

        if (Object.keys(errors).length > 0) {
            req.flash('error', errors);
            return res.redirect('/game/create');
        }

        // Fetch questions from OpenTDB
        const params = {
            amount: numQuestions,
            type: 'multiple'
        };
        
        if (category) {
            params.category = category;
        }

        const response = await axios.get(config.openTDB.baseURL, { params });
        
        if (response.data.response_code !== 0) {
            throw new Error('Failed to fetch questions from OpenTDB');
        }

        const pin = await Game.generatePin();
        const game = await Game.create({
            title,
            pin,
            host_id: req.user.id
        });

        // Save questions to database
        const questions = response.data.results.map(q => ({
            content: q.question,
            correct_answer: q.correct_answer,
            incorrect_answers: q.incorrect_answers,
            time_limit: 20,
            points: 1000,
            game_id: game.id
        }));

        await Question.bulkCreate(questions);

        req.flash('success', 'Game created successfully with questions from OpenTDB!');
        res.redirect(`/game/edit/${game.pin}`);
    } catch (error) {
        console.error('Error creating game:', error);
        req.flash('error', { general: 'Failed to create game' });
        res.redirect('/game/create');
    }
});

// Edit game
router.get('/edit/:pin', isAuthenticated, async (req, res) => {
    try {
        const game = await Game.findOne({
            where: { pin: req.params.pin },
            include: [{
                model: Question,
                order: [['id', 'ASC']]
            }]
        });

        if (!game) {
            req.flash('error', 'Game not found');
            return res.redirect('/game/dashboard');
        }

        if (game.host_id !== req.user.id) {
            req.flash('error', 'Unauthorized');
            return res.redirect('/game/dashboard');
        }

        res.render('game/edit', {
            title: `Edit Game: ${game.title}`,
            game,
            questions: game.Questions
        });
    } catch (error) {
        console.error('Error loading game:', error);
        req.flash('error', 'Failed to load game');
        res.redirect('/game/dashboard');
    }
});

// Game lobby
router.get('/lobby/:pin', async (req, res) => {
    try {
        const game = await Game.findOne({
            where: { pin: req.params.pin },
            include: [
                {
                    model: Player,
                    attributes: ['id', 'nickname', 'is_ready']
                },
                {
                    model: User,
                    as: 'host',
                    attributes: ['username']
                }
            ]
        });

        if (!game) {
            req.flash('error', 'Game not found');
            return res.redirect('/');
        }

        if (game.started_at) {
            return res.redirect(`/game/play/${game.pin}`);
        }

        const isHost = req.user && game.host_id === req.user.id;
        const playerId = req.session.player_id;

        if (!isHost && !playerId) {
            req.flash('error', 'Please join the game first');
            return res.redirect('/');
        }

        // Create a data object for client-side JavaScript
        const clientData = {
            pin: game.pin,
            playerId: playerId || null,
            hostId: game.host_id,
            isHost: isHost
        };

        res.render('game/lobby', {
            title: `Game Lobby: ${game.title}`,
            game,
            isHost,
            playerId,
            clientData: {
                pin: game.pin,
                playerId: playerId || null,
                hostId: game.host_id,
                isHost: isHost
            }
        });
    } catch (error) {
        console.error('Error loading lobby:', error);
        req.flash('error', 'Failed to load game lobby');
        res.redirect('/');
    }
});

// Play game
router.get('/play/:pin', async (req, res) => {
    try {
        const game = await Game.findOne({
            where: { pin: req.params.pin }
        });

        if (!game) {
            req.flash('error', 'Game not found');
            return res.redirect('/');
        }

        if (!game.started_at) {
            return res.redirect(`/game/lobby/${game.pin}`);
        }

        const playerId = req.session.player_id;
        if (!playerId) {
            req.flash('error', 'Please join the game first');
            return res.redirect('/');
        }

        const player = await Player.findOne({
            where: { id: playerId, game_id: game.id }
        });

        if (!player) {
            req.flash('error', 'Player not found');
            return res.redirect('/');
        }

        res.render('game/play', {
            title: `Playing: ${game.title}`,
            game,
            player,
            clientData: {
                pin: game.pin,
                playerId: player.id,
                hostId: game.host_id,
                isHost: false
            }
        });
    } catch (error) {
        console.error('Error loading game:', error);
        req.flash('error', 'Failed to load game');
        res.redirect('/');
    }
});

// Host game
router.get('/host/:pin', isAuthenticated, async (req, res) => {
    try {
        const game = await Game.findOne({
            where: { pin: req.params.pin },
            include: [{
                model: Question,
                order: [['id', 'ASC']]
            }]
        });

        if (!game) {
            req.flash('error', 'Game not found');
            return res.redirect('/game/dashboard');
        }

        if (game.host_id !== req.user.id) {
            req.flash('error', 'Unauthorized');
            return res.redirect('/game/dashboard');
        }

        res.render('game/host', {
            title: `Hosting: ${game.title}`,
            game,
            questions: game.Questions,
            clientData: {
                pin: game.pin,
                playerId: null,
                hostId: game.host_id,
                isHost: true
            }
        });
    } catch (error) {
        console.error('Error loading host view:', error);
        req.flash('error', 'Failed to load game');
        res.redirect('/game/dashboard');
    }
});

module.exports = router;
