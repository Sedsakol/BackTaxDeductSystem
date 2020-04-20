module.exports = (sequelize, Sequelize) => {
    const user_type = sequelize.define(
        'user_type',
        {
            userId: {
                type: Sequelize.INTEGER,
                field: 'user_id',
                primaryKey: true
            },
            usertype: {
                type: Sequelize.INTEGER,
                field: 'usertype'
            },
            usertype1: {
                type: Sequelize.FLOAT,
                field: 'usertype1'
            },
            usertype2: {
                type: Sequelize.FLOAT,
                field: 'usertype2'
            },
            usertype3: {
                type: Sequelize.FLOAT,
                field: 'usertype3'
            },
        },
        {
            timestamps: false,
            freezeTableName: true
        }
    );
    return user_type;
};