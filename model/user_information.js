module.exports = (sequelize, Sequelize) => {
    const user_information = sequelize.define(
        'user_information',
        {
            userId: {
                type: Sequelize.INTEGER,
                field: 'user_id',
                primaryKey: true
            },
            username: {
                type: Sequelize.STRING,
                field: 'username'
            },
            password: {
                type: Sequelize.STRING,
                field: 'password'
            },
            firstName: {
                type: Sequelize.STRING,
                field: 'first_name'
            },
            lastName: {
                type: Sequelize.STRING,
                field: 'last_name'
            },
            email: {
                type: Sequelize.STRING,
                field: 'email'
            },
            birth: {
                type: Sequelize.DATE,
                field: 'birth'
            }
        },
        {
            timestamps: false,
            freezeTableName: true
        }
    );
    return user_information;
};