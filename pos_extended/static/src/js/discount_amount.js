odoo.define('hsr_pos.discount_amount', function (require) {
"use strict";

var screens = require('point_of_sale.screens');

var DiscountAmountButton = screens.ActionButtonWidget.extend({
    template: 'DiscountAmountButton',
    button_click: function(){
        var self = this;
        this.gui.show_popup('number',{
            'title': 'Discount Amount',
            'value': this.pos.config.chef_discount_amount,
            'confirm': function(val) {
                val = Math.round(Math.max(0,Math.min(this.pos.config.chef_discount_amount,val)));
                self.apply_discount(val);
            },
        });
    },
    apply_discount: function(pc) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.chef_discount_product_id[0]);

        // Remove existing discounts
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add discount
        var discount = - pc ;

        if( discount < 0 ){
            order.add_product(product, { price: discount });
        }
    },
});

screens.define_action_button({
    'name': 'discount',
    'widget': DiscountAmountButton,
    'condition': function(){
        return this.pos.config.chef_iface_discount && this.pos.config.chef_discount_product_id;
    },
});


});

