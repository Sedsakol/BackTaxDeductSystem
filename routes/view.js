
// import lib
const express = require('express');
const db = require("../config/db.config.js");
// define variable
const sequelize = db.sequelize;

sequelize
  .authenticate()
  .then(() => {
    console.log('Connection to Database has been established successfully.');
  })
  .catch(err => {
    console.error('Unable to connect to the database:', err);
  });

//ใช้เมื่อมีการแก้ไขใน database ใหม่
// db.sequelize.sync(); 


const userInformation = db.user_information;
const userStatus = db.user_status;
const userType = db.user_type;

const route = express.Router();

route.get('/test1' , async (req, res, next) => {
  console.log('body::==', req.body);
  console.log('params::==', req.params);
  const entry = await userInformation.findAll();
  res.json(entry);
});

route.get('/test' , async (req, res, next) => {
  console.log('body::==', req.body);
  console.log('params::==', req.params);
  res.json({ message : 'test'});
});

module.exports = route;