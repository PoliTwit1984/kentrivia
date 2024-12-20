const express = require('express');
const router = express.Router();
const { Game, Player } = require('../models');

// Home page
router.get('/', async (req, res) => {
    try {
        // Check for game PIN in query params (for QR code scans)
        const pin = req.query.pin;
        if (pin) {
            const game = await Game.findOne({ where: { pin } });
            if (game) {
                if (game.started_at) {
                    req.flash('error', 'Game has already started');
                    return res.redirect('/');
                }
                return res.render('main/join', { 
                    title: 'Join Game',
                    pin
                });
            }
        }

        res.render('main/index', { 
            title: 'Welcome to KenTrivia'
        });
    } catch (error) {
        console.error('Error loading home page:', error);
        req.flash('error', 'Failed to load page');
        res.redirect('/');
    }
});

// Join game
router.post('/join', async (req, res) => {
    const { pin, nickname } = req.body;
    const errors = {};

    try {
        if (!pin) {
            errors.pin = 'Game PIN is required';
        }

        if (!nickname || nickname.length < 2 || nickname.length > 20) {
            errors.nickname = 'Nickname must be between 2 and 20 characters';
        }

        if (Object.keys(errors).length > 0) {
            req.flash('error', errors);
            return res.redirect('/');
        }

        const game = await Game.findOne({ where: { pin } });
        if (!game) {
            req.flash('error', 'Game not found');
            return res.redirect('/');
        }

        if (game.started_at) {
            req.flash('error', 'Game has already started');
            return res.redirect('/');
        }

        const player = await Player.create({
            game_id: game.id,
            nickname
        });

        req.session.player_id = player.id;
        res.redirect(`/game/lobby/${pin}`);
    } catch (error) {
        console.error('Error joining game:', error);
        req.flash('error', 'Failed to join game');
        res.redirect('/');
    }
});

// How to play page
router.get('/how-to-play', (req, res) => {
    res.render('main/how-to-play', { 
        title: 'How to Play'
    });
});

// CSRF token refresh
router.get('/csrf-token', (req, res) => {
    res.json({ token: req.csrfToken() });
});

module.exports = router;
