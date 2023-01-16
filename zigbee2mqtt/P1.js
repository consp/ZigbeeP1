const fz = require('zigbee-herdsman-converters/converters/fromZigbee');
const tz = require('zigbee-herdsman-converters/converters/toZigbee');
const exposes = require('zigbee-herdsman-converters/lib/exposes');
const reporting = require('zigbee-herdsman-converters/lib/reporting');
const extend = require('zigbee-herdsman-converters/lib/extend');
const e = exposes.presets;
const ea = exposes.access;

const fzLocal = {
    conspunit: {
        cluster: 'haElectricalMeasurement',
        type: ['attributeReport', 'readResponse'],
        convert: async (model, msg, publish, options, meta) => {
            const attr = msg.data;
            const powerDivisor = attr['powerDivisor'];
            const powerMultiplier = attr['powerMultiplier'];
            const measurementType = attr['measurementType'];
            const acVoltageMultiplier = attr['acVoltageMultiplier'];
            const acVoltageDivisor = attr['acVoltageDivisor'];
            const acCurrentMultiplier = attr['acCurrentMultiplier'];
            const acCurrentDivisor = attr['acCurrentDivisor'];
            const ret = {};
            var P1 = "";

            if (attr.hasOwnProperty('totalActivePower')) {
                ret['power_total'] = attr['totalActivePower'] * powerMultiplier / powerDivisor;
                p1power = ret['power_total'];
            } else {
                p1power = meta['state']['power_total'];
            }
            if (attr.hasOwnProperty('activePower')) {
                ret['power'] = attr['activePower'] * powerMultiplier / powerDivisor;
            }
            if (attr.hasOwnProperty('activePowerPhB')) {
                ret['power_b'] = attr['activePowerPhB'] * powerMultiplier / powerDivisor;
            }
            if (attr.hasOwnProperty('activePowerPhC')) {
                ret['power_c'] = attr['activePowerPhC'] * powerMultiplier / powerDivisor;
            }
            if (attr.hasOwnProperty('rmsVoltage')) {
                ret['voltage'] = attr['rmsVoltage'] * acVoltageMultiplier / acVoltageDivisor;
            }
            if (attr.hasOwnProperty('rmsVoltagePhB')) {
                ret['voltage_b'] = attr['rmsVoltagePhB'] * acVoltageMultiplier / acVoltageDivisor;
            }
            if (attr.hasOwnProperty('rmsVoltagePhC')) {
                ret['voltage_c'] = attr['rmsVoltagePhC'] * acVoltageMultiplier / acVoltageDivisor;
            }
            if (attr.hasOwnProperty('rmsVoltage')) {
                ret['current'] = attr['rmsCurrent'] * acCurrentMultiplier / acCurrentDivisor;
            }
            if (attr.hasOwnProperty('rmsVoltagePhB')) {
                ret['current_b'] = attr['rmsCurrentPhB'] * acCurrentMultiplier / acCurrentDivisor;
            }
            if (attr.hasOwnProperty('rmsVoltagePhC')) {
                ret['current_c'] = attr['rmsCurrentPhC'] * acCurrentMultiplier / acCurrentDivisor;
            }
            const state = meta['state']
            var P1 = (state['energy_t1'] * 1000).toString() + ";" + (state['energy_t2'] * 1000).toString() + ";" + (state['energy_t1_return'] * 1000).toString() + ";" + (state['energy_t2_return'] * 1000).toString() + ";" + p1power.toString() + ";0";
            console.log(meta);
            ret['P1'] = P1;
            return ret;
        }
    },
    conspunit2: {
        cluster: 'seMetering',
        type: ['attributeReport'],
        convert: async (model, msg, publish, options, meta) => {
            const attr = msg.data;
            const powerDivisor = attr['divisor'];
            const powerMultiplier = attr['multiplier'];
            const ret = {};
            const state = meta['state'];
            var et1 = 0, et2 = 0, et1r = 0, et2r = 0;

            if (attr.hasOwnProperty('currentSummDelivered') && msg.endpoint.ID == 1) {
                ret['energy'] = attr['currentSummDelivered'][1] * powerMultiplier / powerDivisor;
            }
            if (attr.hasOwnProperty('currentSummDelivered') && msg.endpoint.ID == 2) {
                ret['gas'] = attr['currentSummDelivered'][1] * powerMultiplier / powerDivisor;
            }
            if (attr.hasOwnProperty('currentTier1SummDelivered') && msg.endpoint.ID == 1) {
                ret['energy_t1'] = attr['currentTier1SummDelivered'][1] * powerMultiplier / powerDivisor;
                et1 = ret['energy_t1'];
            } else {
                et1 = state['energy_t1'];
            }
            if (attr.hasOwnProperty('currentTier1SummReceived') && msg.endpoint.ID == 1) {
                ret['energy_t1_return'] = attr['currentTier1SummReceived'][1] * powerMultiplier / powerDivisor;
                et1r = ret['energy_t1_return'];
            } else {
                et1r = state['energy_t1_return'];
            }
            if (attr.hasOwnProperty('currentTier2SummDelivered') && msg.endpoint.ID == 1) {
                ret['energy_t2'] = attr['currentTier2SummDelivered'][1] * powerMultiplier / powerDivisor;
                et2 = ret['energy_t2'];
            } else {
                et2 = state['energy_t2'];
            }
            if (attr.hasOwnProperty('currentTier2SummReceived') && msg.endpoint.ID == 1) {
                ret['energy_t2_return'] = attr['currentTier2SummReceived'][1] * powerMultiplier / powerDivisor;
                et2r = ret['energy_t2_return'];
            } else {
                et2r = state['energy_t2_return'];
            }

            var P1 = (et1 * 1000).toString() + ";" + (et2 * 1000).toString() + ";" + (et1r * 1000).toString() + ";" + (et2r * 1000).toString() + ";" + state['power_total'].toString() + ";0";
            ret['P1'] = P1;
            return ret;
        }
    }
};

const definition = {
    zigbeeModel: ['Zigbee P1 Meter'], // The model ID from: Device with modelID 'lumi.sens' is not supported.
    model: 'P1', // Vendor model number, look on the device for a model number
    vendor: 'consp', // Vendor of the device (only used for documentation and startup logging)
    description: 'Custom P1 meter using XBee3', // Description of the device, copy from vendor site. (only used for documentation and startup logging)
    fromZigbee: [fzLocal.conspunit, fzLocal.conspunit2], // We will add this later
    toZigbee: [], // Should be empty, unless device can be controlled (e.g. lights, switches).
    exposes: [
        e.energy(),
        exposes.numeric('power_total', ea.STATE).withDescription("Instantaneous measured power (combined)").withUnit("W"),
        e.power(),
        exposes.numeric('power_b', ea.STATE).withDescription("Instantaneous measured power (phase B)").withUnit("W"),
        exposes.numeric('power_c', ea.STATE).withDescription("Instantaneous measured power (phase C)").withUnit("W"),
        //e.power_factor(),
        e.voltage(),
        exposes.numeric('voltage_b', ea.STATE).withDescription("Measured electrical potential value (phase B)").withUnit("V"),
        exposes.numeric('voltage_c', ea.STATE).withDescription("Measured electrical potential value (phase C)").withUnit("V"),
        e.current(), 
        exposes.numeric('current_b', ea.STATE).withDescription("Instantaneous measured electrical current (phase B)").withUnit("A"),
        exposes.numeric('current_c', ea.STATE).withDescription("Instantaneous measured electrical current (phase C)").withUnit("A"),
        exposes.numeric('energy_t1', ea.STATE).withDescription("T1 Power from grid").withUnit("kWh"),
        exposes.numeric('energy_t1_return', ea.STATE).withDescription("T1 Power to grid").withUnit("kWh"),
        exposes.numeric('energy_t2', ea.STATE).withDescription("T2 Power from grid").withUnit("kWh"),
        exposes.numeric('energy_t2_return', ea.STATE).withDescription("T2 Power to grid").withUnit("kWh"),
        exposes.numeric('gas', ea.STATE).withDescription("Gas consumed").withUnit("m³"),
        exposes.text('P1', ea.STATE).withDescription("Domotics dummy P1 value"),
        ],
    configure: async (device, coordinatorEndpoint, logger) => {
            const endpoint = device.getEndpoint(1);
            const endpoint2 = device.getEndpoint(2);
            await reporting.bind(endpoint, coordinatorEndpoint, ['haElectricalMeasurement']);
            await reporting.bind(endpoint, coordinatorEndpoint, ['seMetering']);
            await reporting.bind(endpoint2, coordinatorEndpoint, ['seMetering']);
    },
};

module.exports = definition;

