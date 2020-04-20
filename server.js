// import express & define port = 3000
const express = require('express');
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();

var corsOptions = {
    origin: "http://localhost:8081"
};

app.use(cors(corsOptions));

// parse requests of content-type - application/json
app.use(express.json());

// parse requests of content-type - application/x-www-form-urlencoded
app.use(express.urlencoded({ extended: false }));


// simple route
app.get("/", (req, res) => {
    console.log(' "Welcome to tax deduct system."');
});

//add router
const rounter = require('./routes/view');
app.use('/view',rounter)

// set port, listen for requests
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}.`);
});

