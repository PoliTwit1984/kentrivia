require('dotenv').config();

module.exports = {
    app: {
        port: parseInt(process.env.PORT) || 5001,
        host: process.env.HOST || '127.0.0.1',
        env: process.env.NODE_ENV || 'development',
        secretKey: process.env.SECRET_KEY || 'your-secret-key'
    },
    db: {
        database: process.env.DB_NAME || 'kentrivia',
        username: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASS || '',
        host: process.env.DB_HOST || 'localhost',
        dialect: 'postgres',
        pool: {
            max: 5,
            min: 0,
            acquire: 30000,
            idle: 10000
        }
    },
    session: {
        secure: process.env.NODE_ENV === 'production',
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000 // 24 hours
    },
    openTDB: {
        baseURL: 'https://opentdb.com/api.php',
        categories: [
            { id: 9, name: 'General Knowledge' },
            { id: 10, name: 'Entertainment: Books' },
            { id: 11, name: 'Entertainment: Film' },
            { id: 12, name: 'Entertainment: Music' },
            { id: 14, name: 'Entertainment: Television' },
            { id: 15, name: 'Entertainment: Video Games' },
            { id: 17, name: 'Science & Nature' },
            { id: 18, name: 'Science: Computers' },
            { id: 19, name: 'Science: Mathematics' },
            { id: 21, name: 'Sports' },
            { id: 22, name: 'Geography' },
            { id: 23, name: 'History' },
            { id: 24, name: 'Politics' },
            { id: 25, name: 'Art' },
            { id: 27, name: 'Animals' },
            { id: 28, name: 'Vehicles' },
            { id: 29, name: 'Entertainment: Comics' },
            { id: 30, name: 'Science: Gadgets' },
            { id: 31, name: 'Entertainment: Japanese Anime & Manga' },
            { id: 32, name: 'Entertainment: Cartoon & Animations' }
        ]
    }
};
