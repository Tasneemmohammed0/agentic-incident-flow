(function executeRule(current, previous /*null when async*/) {
    try {
        var payload = {
            "incident_sys_id": current.getValue('sys_id'),
            "number": current.getValue('number'),
            "short_description": current.getValue('short_description'),
            "description": current.getValue('description'),
            "priority": parseInt(current.getValue('priority'), 10)
        };

        var r = new sn_ws.RESTMessageV2();
        // Replace YOUR_ENDPOINT with your public ngrok URL, keep /webhook:
        r.setEndpoint('YOUR_ENDPOINT/webhook');
        r.setHttpMethod('POST');
        r.setRequestHeader('Content-Type', 'application/json');
        r.setRequestBody(JSON.stringify(payload));
        r.executeAsync();

        gs.info('Task0: sent incident ' + current.getValue('number'));
    } catch (ex) {
        gs.error('Task0: failed to send incident: ' + ex.message);
    }
})(current, previous);
