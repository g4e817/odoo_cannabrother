PRODUCT_REL = "woo_product"
ORDER_REL = "woo_order"
TAXE_REL ="woo_taxe"
CUSTOMER_REL ="woo_customer"

def product_x2odoo(data):
    return {
        "name": data['name'],
        "description": data['permalink'],
        "list_price": data["sale_price"],
        "standard_price": data["regular_price"]
    }


def product_odoo2x(odoo):
    return {
        "name":
        odoo.name,
        "description":
        odoo.description,
        "sale_price":
        odoo.list_price,
        "regular_price":
        odoo.standard_price,
        "attributes": [{
            "id":
            attr.id,
            "name":
            attr.attribute_id.name,
            "variation":
            attr.attribute_id.create_variant == 'instantly',
            "options":
            [option.name for option in attr.product_template_value_ids]
        } for attr in odoo.attribute_line_ids]
    }


def x_product2ref(data):
    return data["id"]


def x_product_get_all():
    return wcapi_request("get", "products")


def x_product_create(odoo):
    data = product_odoo2x(odoo)
    res = wcapi_request("post", "products", data)
    return res['id']


def x_product_update(ref, odoo):
    data = product_odoo2x(odoo)
    res = wcapi_request("put", "products/%s" % ref, data)
    return ref


def odoo_product_get_all(to_create=False, to_update=False):
    all_records = env["product.product"].search([])
    if to_create and to_update:
        return all_records
    linked = all_records.search_links(PRODUCT_REL).mapped(
        lambda link: link.odoo)
    if to_create:
        return all_records - linked
    if to_update:
        return linked


def odoo_product_create(data):
    vals = product_x2odoo(data)
    log("env[\"product.product\"].create(%s)" % vals, LOG_DEBUG)
    return env["product.product"].create(vals)


def odoo_product_update(odoo, data):
    vals = product_x2odoo(data)
    log("%s.write(%s)" % (odoo, vals), LOG_DEBUG)
    return odoo.write(vals)


PRODUCT_SYNC = {
    "relation": PRODUCT_REL,
    "x": {
        "get_ref": x_product2ref,
        "create": x_product_create,
        "update": x_product_update,
    },
    "odoo": {
        "create": odoo_product_create,
        "update": odoo_product_update,
    }
}


def order_x2odoo(data):
    data_state = data['status']

    state = 'draft'
    currency_id = env['res.currency'].sudo().search([('code', '=',
                                                      data['currency'])])
    if data_state in ['pending', 'on-hold']:
        state = 'draft'
    elif data_state in ['processing']:
        state = 'sale'
    elif data_state in ['cancelled', 'refunded', 'trash']:
        state = 'cancel'
    partner_id = partner_shipping_id = env['res.partner'].sudo()
    if data['billing']:
        partner_id = partner_id.search([('email', '=',
                                         data['billing']['email'])])
    if data['shipping']:
        partner_shipping_id = env['res.partner'].sudo().search([
            ('email', '=', data['billing']['email'])
        ])
        if not partner_shipping_id:
            partner_shipping_id = partner_id
    order_line = []
    shipping_line = []
    for line in data['line_items']:
        tax_ids = env['account.tax'].sudo().search([
            ('name', 'in',
             [tax_line['label'] for tax_line in line['tax_lines']])
        ]).ids
        discount = ((line['price'] * line['quantity']) - line['subtotal'])
        order_line.append((0, 0, {
            'product_id': line['product_id'],
            'price_unit': line['price'],
            'product_uom_qty': line['quantity'],
            'taxe_ids': [(6, 0, tax_ids)],
            'discount': discount
        }))
    for shipping_line in data['shipping_lines']:
        tax_ids = env['account.tax'].sudo().search([
            ('name', 'in',
             [tax_line['label'] for tax_line in shipping_line['tax_lines']])
        ]).ids
        discount = ((shipping_line['price'] * shipping_line['quantity']) -
                    shipping_line['subtotal'])
        order_line.append((0, 0, {
            'product_id': shipping_line['product_id'],
            'price_unit': shipping_line['price'],
            'product_uom_qty': shipping_line['quantity'],
            'taxe_ids': [(6, 0, tax_ids)],
            'discount': discount
        }))
    for fee_line in data['fee_lines']:
        tax_ids = env['account.tax'].sudo().search([
            ('name', 'in',
             [tax_line['label'] for tax_line in fee_line['tax_lines']])
        ]).ids
        discount = ((fee_line['price'] * fee_line['quantity']) -
                    fee_line['subtotal'])
        order_line.append((0, 0, {
            'product_id': fee_line['product_id'],
            'price_unit': fee_line['price'],
            'product_uom_qty': fee_line['quantity'],
            'taxe_ids': [(6, 0, tax_ids)],
            'discount': discount
        }))
    return {
        "name": data['number'],
        "state": state,
        "currency_id": currency_id.id,
        "partner_id": partner_id.id,
        "partner_invoice_id": partner_id.id,
        "partner_shippind_id": partner_shipping_id.id,
        "order_line": order_line
    }


def order_odoo2x(odoo):
    line_items=[{"product_id":line.product_id.id,
                 "price":line.price_unit,
                 "quantity":line.product_uom_qty}for line in odoo.order_line]
    return {
        "number":
        odoo.name,
        "status":
        odoo.state
        } 
    


def x_order2ref(data):
    return data["id"]


def x_order_get_all():
    return wcapi_request("get", "orders")


def x_order_create(odoo):
    data = order_odoo2x(odoo)
    res = wcapi_request("post", "orders", data)
    return res['id']


def x_order_update(ref, odoo):
    data = order_odoo2x(odoo)
    res = wcapi_request("put", "orders/%s" % ref, data)
    return ref


def odoo_order_get_all(to_create=False, to_update=False):
    all_records = env["sale.order"].search([])
    if to_create and to_update:
        return all_records
    linked = all_records.search_links(PRODUCT_REL).mapped(
        lambda link: link.odoo)
    if to_create:
        return all_records - linked
    if to_update:
        return linked


def odoo_order_create(data):
    vals = order_x2odoo(data)
    log("env[\"sale.order\"].create(%s)" % vals, LOG_DEBUG)
    return env["sale.order"].create(vals)


def odoo_order_update(odoo, data):
    vals = order_x2odoo(data)
    log("%s.write(%s)" % (odoo, vals), LOG_DEBUG)
    return odoo.write(vals)


ORDER_SYNC = {
    "relation": ORDER_REL,
    "x": {
        "get_ref": x_order2ref,
        "create": x_order_create,
        "update": x_order_update,
    },
    "odoo": {
        "create": odoo_order_create,
        "update": odoo_order_update,
    }
}

def tax_x2odoo(data):
    return {
        "name": data['label'],
        "description": data['permalink'],
        "list_price": data["sale_price"],
        "standard_price": data["regular_price"]
    }


def tax_odoo2x(odoo):
    return {
        "name":
        odoo.name,
    }


def x_tax2ref(data):
    return data["id"]


def x_tax_get_all():
    return wcapi_request("get", "taxes")


def x_tax_create(odoo):
    data = tax_odoo2x(odoo)
    res = wcapi_request("post", "taxes", data)
    return res['id']


def x_tax_update(ref, odoo):
    data = tax_odoo2x(odoo)
    res = wcapi_request("put", "taxes/%s" % ref, data)
    return ref


def odoo_tax_get_all(to_create=False, to_update=False):
    all_records = env["account.tax"].search([])
    if to_create and to_update:
        return all_records
    linked = all_records.search_links(PRODUCT_REL).mapped(
        lambda link: link.odoo)
    if to_create:
        return all_records - linked
    if to_update:
        return linked


def odoo_tax_create(data):
    vals = tax_x2odoo(data)
    log("env[\"account.tax\"].create(%s)" % vals, LOG_DEBUG)
    return env["account.tax"].create(vals)


def odoo_tax_update(odoo, data):
    vals = tax_x2odoo(data)
    log("%s.write(%s)" % (odoo, vals), LOG_DEBUG)
    return odoo.write(vals)


TAX_SYNC = {
    "relation": TAX_REL,
    "x": {
        "get_ref": x_tax2ref,
        "create": x_tax_create,
        "update": x_tax_update,
    },
    "odoo": {
        "create": odoo_tax_create,
        "update": odoo_tax_update,
    }
}

def customer_x2odoo(data):
    return {
        "name": data['name'],
        "description": data['permalink'],
        "list_price": data["sale_price"],
        "standard_price": data["regular_price"]
    }


def customer_odoo2x(odoo):
    return {
        "name":
        odoo.name,
    }


def x_customer2ref(data):
    return data["id"]


def x_customer_get_all():
    return wcapi_request("get", "customers")


def x_customer_create(odoo):
    data = customer_odoo2x(odoo)
    res = wcapi_request("post", "customers", data)
    return res['id']


def x_customer_update(ref, odoo):
    data = customer_odoo2x(odoo)
    res = wcapi_request("put", "customers/%s" % ref, data)
    return ref


def odoo_customer_get_all(to_create=False, to_update=False):
    all_records = env["res.partner"].search([])
    if to_create and to_update:
        return all_records
    linked = all_records.search_links(PRODUCT_REL).mapped(
        lambda link: link.odoo)
    if to_create:
        return all_records - linked
    if to_update:
        return linked


def odoo_customer_create(data):
    vals = customer_x2odoo(data)
    log("env[\"res.partner\"].create(%s)" % vals, LOG_DEBUG)
    return env["res.partner"].create(vals)


def odoo_customer_update(odoo, data):
    vals = customer_x2odoo(data)
    log("%s.write(%s)" % (odoo, vals), LOG_DEBUG)
    return odoo.write(vals)


PRODUCT_SYNC = {
    "relation": PRODUCT_REL,
    "x": {
        "get_ref": x_customer2ref,
        "create": x_customer_create,
        "update": x_customer_update,
    },
    "odoo": {
        "create": odoo_customer_create,
        "update": odoo_customer_update,
    }
}



#HANDLE

def handle_cron():
    _sync_x2odoo(create=True, update=True)

def handle_button():
    if trigger == "UPDATE_PRODUCTS_WOO2ODOO":
        _sync_x2odoo(update=True)
    elif trigger == "CREATE_PRODUCTS_WOO2ODOO":
        _sync_x2odoo(create=True)
    elif trigger == "SETUP_WOO_WEBHOOKS":
        setup_woo_webhooks()
    else:
        raise Exception("Unknown button: %s" % trigger)


def _sync_x2odoo(create=False, update=False):
    return sync_x2odoo(x_product_get_all(), PRODUCT_SYNC, create=create, update=update)

def setup_woo_webhooks():
    for topic, webhook in (
      ("product.created", webhooks.WOO_PRODUCT_CREATED),
      ("product.updated", webhooks.WOO_PRODUCT_UPDATED),
      ("product.deleted", webhooks.WOO_PRODUCT_DELETED)
      ):
        data = {
          "name": topic,
          "topic": topic,
          "delivery_url": webhook
        }

        wcapi_request("post", "webhooks", data)

def handle_webhook(httprequest):
    data = json.loads(httprequest.data.decode())
    log("Woo payload:\n{}".format(json.dumps(data, indent=4, sort_keys=True)))
    if trigger == "WOO_PRODUCT_CREATED":
        sync_x2odoo([data], PRODUCT_SYNC, create=True)
    elif trigger == "WOO_PRODUCT_UPDATED":
        sync_x2odoo([data], PRODUCT_SYNC, update=True)
    elif trigger == "WOO_PRODUCT_DELETED":
        # TODO
        pass
    
    
    
def handle_cron():
    _sync_orderx2odoo(create=True, update=True)

def handle_button():
if trigger == "UPDATE_ORDERS_WOO2ODOO":
    _sync_orderx2odoo(update=True)
elif trigger == "CREATE_ORDERS_WOO2ODOO":
    _sync_orderx2odoo(create=True)
elif trigger == "SETUP_WOO_WEBHOOKS":
    setup_woo_webhooks()
else:
    raise Exception("Unknown button: %s" % trigger)


def _sync_orderx2odoo(create=False, update=False):
return sync_x2odoo(x_order_get_all(), ORDER_SYNC, create=create, update=update)

def setup_woo_webhooks():
for topic, webhook in (
  ("order.created", webhooks.WOO_ORDER_CREATED),
  ("order.updated", webhooks.WOO_ORDER_UPDATED),
  ("order.deleted", webhooks.WOO_ORDER_DELETED)
  ):
    data = {
      "name": topic,
      "topic": topic,
      "delivery_url": webhook
    }

    wcapi_request("post", "webhooks", data)

def handle_webhook(httprequest):
data = json.loads(httprequest.data.decode())
log("Woo payload:\n{}".format(json.dumps(data, indent=4, sort_keys=True)))
if trigger == "WOO_ORDER_CREATED":
    sync_x2odoo([data], ORDER_SYNC, create=True)
elif trigger == "WOO_ORDER_UPDATED":
    sync_x2odoo([data], ORDER_SYNC, update=True)
elif trigger == "WOO_ORDER_DELETED":
    # TODO
    pass