const express = require('express');
const passport = require('passport');
const router = express.Router();
const { User } = require('../models');
const { Op } = require('sequelize');

// Middleware to check if user is authenticated
const isAuthenticated = (req, res, next) => {
    if (req.isAuthenticated()) {
        return next();
    }
    req.flash('error', 'Please log in to access this page');
    res.redirect('/auth/login');
};

// Login page
router.get('/login', (req, res) => {
    if (req.isAuthenticated()) {
        return res.redirect('/game/dashboard');
    }
    res.render('auth/login', { 
        title: 'Login'
    });
});

// Login handler
router.post('/login', passport.authenticate('local', {
    successRedirect: '/game/dashboard',
    failureRedirect: '/auth/login',
    failureFlash: true
}));

// Register page
router.get('/register', (req, res) => {
    if (req.isAuthenticated()) {
        return res.redirect('/game/dashboard');
    }
    res.render('auth/register', { 
        title: 'Register'
    });
});

// Register handler
router.post('/register', async (req, res) => {
    const { username, email, password, confirm_password } = req.body;
    const errors = {};

    try {
        // Validate input
        if (!username || username.length < 3 || username.length > 20) {
            errors.username = 'Username must be between 3 and 20 characters';
        }

        if (!email || !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
            errors.email = 'Please enter a valid email address';
        }

        if (!password || password.length < 8) {
            errors.password = 'Password must be at least 8 characters';
        }

        if (password !== confirm_password) {
            errors.confirm_password = 'Passwords do not match';
        }

        // Check if username or email already exists
        const existingUser = await User.findOne({
            where: {
                [Op.or]: [
                    { username },
                    { email }
                ]
            }
        });

        if (existingUser) {
            if (existingUser.username === username) {
                errors.username = 'Username already taken';
            }
            if (existingUser.email === email) {
                errors.email = 'Email already registered';
            }
        }

        if (Object.keys(errors).length > 0) {
            req.flash('error', errors);
            return res.redirect('/auth/register');
        }

        // Create user
        const user = await User.create({
            username,
            email,
            password
        });

        // Log in the new user
        req.login(user, (err) => {
            if (err) {
                console.error('Error logging in new user:', err);
                req.flash('error', 'Failed to log in');
                return res.redirect('/auth/login');
            }
            res.redirect('/game/dashboard');
        });
    } catch (error) {
        console.error('Error registering user:', error);
        req.flash('error', 'Failed to register');
        res.redirect('/auth/register');
    }
});

// Logout handler
router.get('/logout', (req, res) => {
    req.logout((err) => {
        if (err) {
            console.error('Error logging out:', err);
        }
        res.redirect('/');
    });
});

module.exports = {
    router,
    isAuthenticated
};
