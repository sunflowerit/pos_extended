odoo.define('hsr_pos.models_inherit', function (require) {
"use strict";
    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');
    var Backbone = window.Backbone;
    var _super_posmodel = models.PosModel.prototype;
    Backbone.Model.include({
        {
            model:  'res.partner',
            fields: ['name','street','city','state_id','country_id','vat','phone','zip','mobile','email','barcode','write_date'],
            domain: [['customer','=',true]], 
            loaded: function(self,partners){
                self.partners = partners;
                self.db.add_partners(partners);
            },
        },
        { 
            model:  'res.company',
            fields: [ 'street','street2','city','zip','logo','currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id' , 'country_id', 'tax_calculation_rounding_method'],
            ids:    function(self){ return [self.user.company_id[0]]; },
            loaded: function(self,companies){ self.company = companies[0]; },
        },{
            model: 'pos.config',
            fields: [],
            domain: function(self){ return [['id','=', self.pos_session.config_id[0]]]; },
            loaded: function(self,configs){
                self.config = configs[0];
                self.config.use_proxy = self.config.iface_payment_terminal || 
                                        self.config.iface_electronic_scale ||
                                        self.config.iface_print_via_proxy  ||
                                        self.config.iface_scan_via_proxy   ||
                                        self.config.iface_cashdrawer;

                if (self.config.company_id[0] !== self.user.company_id[0]) {
                    throw new Error(_t("Error: The Point of Sale User must belong to the same company as the Point of Sale. You are probably trying to load the point of sale as an administrator in a multi-company setup, with the administrator account set to the wrong company."));
                }

                self.db.set_uuid(self.config.uuid);

                var orders = self.db.get_orders();
                for (var i = 0; i < orders.length; i++) {
                    self.pos_session.sequence_number = Math.max(self.pos_session.sequence_number, orders[i].data.sequence_number+1);
                }
           },
        },
    });
        
});

