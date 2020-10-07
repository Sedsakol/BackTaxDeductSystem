const { DataTypes } = require("sequelize/types");

module.exports = (sequelize, Sequelize) => {
    const user_profile = sequelize.define(
        'user_profile',
        {
            user_id: {
                type: Sequelize.INTEGER,
                field: 'user_id',
                primaryKey: true,
                autoIncrement:true,
                allowNull: false
            },
            gender: {
                type: DataTypes.STRING,
                field: 'gender'
            },
            birthday: {
                type: DataTypes.DATE,
                field: 'birthday'
            },
            salary: {
                type: DataTypes.INTEGER,
                field: 'salary'
            },
            other_income: {
                type: DataTypes.INTEGER,
                field: 'other_in come'
            },
            parent_num: {
                type: DataTypes.INTEGER,
                field: 'parent_num'
            },
            child_num: {
                type: DataTypes.INTEGER,
                field: 'child_num'
            },
            infirm: {
                type: DataTypes.INTEGER,
                field: 'infirm'
            },
            facebook_id: {
                type: DataTypes.INTEGER,
                field: 'facebook_id'
            },
            is_deleted: {
                type: DataTypes.BOOLEAN 
            }
        },
        {
            timestamps: false,
            freezeTableName: true
        }
    );
    return user_profile;
};