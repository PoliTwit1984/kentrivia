const { sequelize, User, Game, Question, Player } = require('../models');

async function setupTestData() {
    try {
        // Sync database
        await sequelize.sync({ force: true });
        console.log('Database synced');

        // Create test user
        const user = await User.create({
            username: 'testuser',
            email: 'test@example.com',
            password: 'password123'
        });
        console.log('Test user created');

        // Create test game
        const game = await Game.create({
            title: 'Test Trivia Game',
            pin: '123456',
            host_id: user.id
        });
        console.log('Test game created');

        // Create test questions
        const questions = await Question.bulkCreate([
            {
                game_id: game.id,
                content: 'What is the capital of France?',
                correct_answer: 'Paris',
                incorrect_answers: ['London', 'Berlin', 'Madrid'],
                time_limit: 20,
                points: 1000
            },
            {
                game_id: game.id,
                content: 'Which planet is known as the Red Planet?',
                correct_answer: 'Mars',
                incorrect_answers: ['Venus', 'Jupiter', 'Saturn'],
                time_limit: 20,
                points: 1000
            },
            {
                game_id: game.id,
                content: 'Who painted the Mona Lisa?',
                correct_answer: 'Leonardo da Vinci',
                incorrect_answers: ['Pablo Picasso', 'Vincent van Gogh', 'Michelangelo'],
                time_limit: 20,
                points: 1000
            }
        ]);
        console.log('Test questions created');

        // Create test players
        const players = await Player.bulkCreate([
            {
                game_id: game.id,
                nickname: 'Player1',
                score: 0,
                current_streak: 0,
                is_ready: false
            },
            {
                game_id: game.id,
                nickname: 'Player2',
                score: 0,
                current_streak: 0,
                is_ready: false
            }
        ]);
        console.log('Test players created');

        console.log('\nTest data setup complete!');
        console.log('\nLogin credentials:');
        console.log('Username: testuser');
        console.log('Password: password123');
        console.log('\nGame PIN: 123456');

        process.exit(0);
    } catch (error) {
        console.error('Error setting up test data:', error);
        process.exit(1);
    }
}

setupTestData();
