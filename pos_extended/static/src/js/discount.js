odoo.define('hsr_pos.discount_inherit', function (require) {
"use strict";

    var screens = require('point_of_sale.screens');

    //~ screens.ActionButtonWidget.DiscountButton.include({
    var DiscountButton = screens.ActionButtonWidget.extend({
        template: 'DiscountButton',
        button_click: function(){
            var self = this;
            this.gui.show_popup('number',{
                'title': 'Discount Percentage',
                'value': this.pos.config.discount_pc,
                'confirm': function(val) {
                    val = Math.round(Math.max(0,Math.min(100,val)));
                    self.apply_discount(val);
                },
            });
        },
        apply_discount: function(pc) {
            var order    = this.pos.get_order();
            var lines    = order.get_orderlines();
            //~ var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
            //~ console.log('sssssssss');
            for (var i = 0; i < lines.length; i++) {
                   //~ lines[i].price =  lines[i].price - (lines[i].price * pc/100)
                   if (pc < this.pos.config.discount_pc)
                   {
                       this.gui.show_popup('error',{
                                'title': 'Access Denied',
                                'body':  'You donot have the permission to give  discount more than' + this.pos.config.discount_pc
                            });
                   }
                   else
                   {
                       lines[i].discount =  pc
                       lines[i].discountStr = '' + lines[i].discount;
                    }
                }
            
        },
    });
    screens.define_action_button({
        'name': 'discount',
        'widget': DiscountButton,
        'condition': function(){
            return this.pos.config.chef_iface_discount;
        },
   });

});
