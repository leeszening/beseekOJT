window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        open_modal: function(n_clicks) {
            if (n_clicks > 0) {
                return 'triggered';
            }
            return '';
        }
    }
});
