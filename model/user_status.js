module.exports = (sequelize, Sequelize) => {
    const user_status = sequelize.define(
        'user_status',
        {
            userStatusId: {
                type: Sequelize.INTEGER,
                field: 'user_status_id',
                primaryKey: true
            },
            userId: {
                type: Sequelize.INTEGER,
                field: 'user_id',
                required: true ,
                allowNull: false
            },
            income: {
                type: Sequelize.DOUBLE,
                field: 'income'
            },
            maritalStatus: {
                type: Sequelize.INTEGER,
                field: 'marital_status'
            },
            children: {
                type: Sequelize.INTEGER,
                field: 'children'
            },
            parent: {
                type: Sequelize.INTEGER,
                field: 'parent'
            },
            buildHouseInterest: {
                type: Sequelize.DOUBLE,
                field: 'build_house_interest'
            },
            lifeInsurance: {
                type: Sequelize.DOUBLE,
                field: 'life_insurance'
            },
            pensionInsurance: {
                type: Sequelize.DOUBLE,
                field: 'pension _insurance'
            },
            RMF: {
                type: Sequelize.DOUBLE,
                field: 'rmf'
            },
            SSF: {
                type: Sequelize.DOUBLE,
                field: 'ssf'
            },
            donate: {
                type: Sequelize.DOUBLE,
                field: 'donate'
            },
            providentFund: {
                type: Sequelize.DOUBLE,
                field: 'provident_fund'
            },
        },
        {
            timestamps: false,
            freezeTableName: true
        }
    );
    return user_status;
};