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
    }
};
