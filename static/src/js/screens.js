odoo.define('hsr_pos.screens_inherit', function (require) {
"use strict";



    var screens = require('point_of_sale.screens');
    var chrome = require('point_of_sale.chrome');
    var multiprint = require('pos_restaurant.multiprint');
    var printbill = require('pos_restaurant.printbill');
    var core = require('web.core');
    var _t = core._t;


    /* --------- The Order Widget --------- */

    // Displays the current Order.

    screens.OrderWidget.include({
        set_value: function(val) {
            var order = this.pos.get_order();
            if (order.get_selected_orderline()) {
                var mode = this.numpad_state.get('mode');
                if( mode === 'quantity'){
                    order.get_selected_orderline().set_quantity(val);
                }else if( mode === 'discount'){
                    order.get_selected_orderline().set_discount(val);
                }else if( mode === 'price'){ 
                    if (this.check_permission() == true){
                        order.get_selected_orderline().set_unit_price(val);
                    }
                }
            }
        },
        check_permission: function(){
            var order = this.pos.get_order(); 
             if (order.pos.user.role =='manager')
                {
                    return true;
                }
                else {
                    this.gui.show_popup('error',{
                        'title': 'Access Denied',
                        'body':  'You donot have the permission'
                    });
                }
        },
        change_selected_order: function() {
            if (this.pos.get_order()) {
                this.bind_order_events();
                this.numpad_state.reset();
                this.renderElement();
            }
        },
        orderline_add: function(){
            this.numpad_state.reset();
            this.renderElement('and_scroll_to_bottom');
        },
        orderline_remove: function(line){
            //~ this.check_permission();
            //~ if (this.check_permission() == true ){
                this.remove_orderline(line);
                this.numpad_state.reset();
                this.update_summary();
            //~ }
        },
        orderline_change: function(line){
            this.rerender_orderline(line);
            this.update_summary();
        },
        bind_order_events: function() {
            var order = this.pos.get_order();
                order.unbind('change:client', this.update_summary, this);
                order.bind('change:client',   this.update_summary, this);
                order.unbind('change',        this.update_summary, this);
                order.bind('change',          this.update_summary, this);

            var lines = order.orderlines;
                lines.unbind('add',     this.orderline_add,    this);
                lines.bind('add',       this.orderline_add,    this);
                lines.unbind('remove',  this.orderline_remove, this);
                lines.bind('remove',    this.orderline_remove, this); 
                lines.unbind('change',  this.orderline_change, this);
                lines.bind('change',    this.orderline_change, this);

        },
        get_roundoff: function() {
            var total = this.get_total_without_tax() + this.get_total_tax();
            var remain = ((total*100)%100);
            var roundoff = 0;
            if(remain){
                        if (remain < 50) {  roundoff =  (-remain)/100;}
                        else { roundoff = (100-remain)/100;}
                    }
            return roundoff;
        },
        get_total_with_tax: function() {
            return this.get_total_without_tax() + this.get_total_tax() + this.get_roundoff();
        },
        export_as_JSON: function() {
            var orderLines, paymentLines;
            orderLines = [];
            this.orderlines.each(_.bind( function(item) {
                return orderLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            paymentLines = [];
            this.paymentlines.each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            return {
                name: this.get_name(),
                amount_paid: this.get_total_paid(),
                amount_total: this.get_total_with_tax(),
                amount_roundoff: this.get_roundoff(),
                amount_tax: this.get_total_tax(),
                amount_return: this.get_change(),
                lines: orderLines,
                statement_ids: paymentLines,
                pos_session_id: this.pos_session_id,
                partner_id: this.get_client() ? this.get_client().id : false,
                user_id: this.pos.cashier ? this.pos.cashier.id : this.pos.user.id,
                uid: this.uid,
                sequence_number: this.sequence_number,
                creation_date: this.creation_date,
                fiscal_position_id: this.fiscal_position ? this.fiscal_position.id : false
            };
        },
        
    });
    
    screens.NumpadWidget.include({
        clickDeleteLastChar: function() {
             //~ if (this.check_permission() == true){
            return this.state.deleteLastChar();
             //~ }
        },
        check_permission: function(){
            var order = this.pos.get_order(); 
             if (order.pos.user.role =='manager')
                {
                    return true;
                }
                else {
                    this.gui.show_popup('error',{
                        'title': 'Access Denied',
                        'body':  'You donot have the permission'
                    });
                }
        },
    });


    
    chrome.OrderSelectorWidget.include({
        deleteorder_click_handler: function(event, $el) {
            var self  = this;
            //~ console.log('test');
            var order = this.pos.get_order(); 
            if (!order) {
                return;
            } else if ( !order.is_empty() ){
                this.gui.show_popup('confirm',{
                    'title': _t('Destroy Current Order ?'),
                    'body': _t('You will lose any data associated with the current order ?'),
                    confirm: function(){
                        self.pos.delete_current_order();
                    },
                });
            } else {
                this.pos.delete_current_order();
            }
        },
    });
    
    


});

    

