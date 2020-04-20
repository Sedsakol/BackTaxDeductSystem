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
                type: Sequelize.INTEGER,
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
                type: Sequelize.INTEGER,
                field: 'build_house_interest'
            },
            lifeInsurance: {
                type: Sequelize.INTEGER,
                field: 'life_insurance'
            },
            pensionInsurance: {
                type: Sequelize.INTEGER,
                field: 'pension _insurance'
            },
            RMF: {
                type: Sequelize.INTEGER,
                field: 'rmf'
            },
            SSF: {
                type: Sequelize.INTEGER,
                field: 'ssf'
            },
            donate: {
                type: Sequelize.INTEGER,
                field: 'donate'
            },
            providentFund: {
                type: Sequelize.INTEGER,
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