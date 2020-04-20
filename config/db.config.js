const Sequelize = require('sequelize');
const env = require('./env');
const sequelize = new Sequelize(env.database, env.username, env.password, {
  host: env.host,
  dialect: env.dialect,
  operatorsAliases: false,

  pool: {
    max: env.max,
    min: env.pool.min,
    acquire: env.pool.acquire,
    idle: env.pool.idle
  }
});

const db = {};
db.Sequelize = Sequelize;
db.sequelize = sequelize;

//import model
db.user_information = require('../model/user_information.js')(sequelize, Sequelize);
db.user_status = require('../model/user_status.js')(sequelize, Sequelize);
db.user_type = require('../model/user_type.js')(sequelize, Sequelize);

//associations

db.user_information.hasMany(db.user_status, { foreignKey: 'userId' ,tragetkey: 'userId'});
db.user_information.belongsTo(db.user_type, { foreignKey: 'userId' ,tragetkey: 'userId'});


module.exports = db;