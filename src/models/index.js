const { Sequelize, DataTypes } = require('sequelize');
const bcrypt = require('bcrypt');
const config = require('../config');

// Initialize Sequelize
const sequelize = new Sequelize(config.db.database, config.db.username, config.db.password || '', {
    host: config.db.host,
    dialect: config.db.dialect,
    logging: false
});

// Define models
const User = sequelize.define('User', {
    username: {
        type: DataTypes.STRING,
        allowNull: false,
        unique: true,
        validate: {
            len: [3, 20]
        }
    },
    email: {
        type: DataTypes.STRING,
        allowNull: false,
        unique: true,
        validate: {
            isEmail: true
        }
    },
    password: {
        type: DataTypes.STRING,
        allowNull: false
    }
}, {
    hooks: {
        beforeCreate: async (user) => {
            user.password = await bcrypt.hash(user.password, 10);
        }
    }
});

User.prototype.checkPassword = async function(password) {
    return bcrypt.compare(password, this.password);
};

const Game = sequelize.define('Game', {
    title: {
        type: DataTypes.STRING,
        allowNull: false,
        validate: {
            len: [3, 64]
        }
    },
    pin: {
        type: DataTypes.STRING(6),
        allowNull: false,
        unique: true
    },
    is_active: {
        type: DataTypes.BOOLEAN,
        defaultValue: true
    },
    started_at: {
        type: DataTypes.DATE
    },
    ended_at: {
        type: DataTypes.DATE
    },
    current_question_index: {
        type: DataTypes.INTEGER,
        defaultValue: -1
    },
    current_question_started_at: {
        type: DataTypes.DATE
    }
});

Game.generatePin = async function() {
    let pin;
    do {
        pin = Math.floor(100000 + Math.random() * 900000).toString();
    } while (await this.findOne({ where: { pin } }));
    return pin;
};

const Question = sequelize.define('Question', {
    content: {
        type: DataTypes.TEXT,
        allowNull: false
    },
    correct_answer: {
        type: DataTypes.STRING,
        allowNull: false
    },
    incorrect_answers: {
        type: DataTypes.JSON,
        allowNull: false,
        defaultValue: []
    },
    time_limit: {
        type: DataTypes.INTEGER,
        defaultValue: 20
    },
    points: {
        type: DataTypes.INTEGER,
        defaultValue: 1000
    }
});

const Player = sequelize.define('Player', {
    nickname: {
        type: DataTypes.STRING,
        allowNull: false,
        validate: {
            len: [2, 20]
        }
    },
    score: {
        type: DataTypes.INTEGER,
        defaultValue: 0
    },
    current_streak: {
        type: DataTypes.INTEGER,
        defaultValue: 0
    },
    is_ready: {
        type: DataTypes.BOOLEAN,
        defaultValue: false
    }
});

const Answer = sequelize.define('Answer', {
    answer_text: {
        type: DataTypes.STRING,
        allowNull: false
    },
    is_correct: {
        type: DataTypes.BOOLEAN,
        allowNull: false
    },
    response_time: {
        type: DataTypes.FLOAT,
        allowNull: false
    },
    points_awarded: {
        type: DataTypes.INTEGER,
        defaultValue: 0
    }
});

// Define relationships
Game.belongsTo(User, { as: 'host', foreignKey: 'host_id' });
Game.hasMany(Question);
Question.belongsTo(Game);

Game.hasMany(Player);
Player.belongsTo(Game);

Question.hasMany(Answer);
Answer.belongsTo(Question);

Player.hasMany(Answer);
Answer.belongsTo(Player);

module.exports = {
    sequelize,
    User,
    Game,
    Question,
    Player,
    Answer
};
