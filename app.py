//@version=6
strategy("Brahmaastra VCP + 90D S&R", overlay=true, max_lines_count=100, max_labels_count=100, initial_capital=100000, default_qty_type=strategy.fixed, default_qty_value=1)

// ==========================================
// ⚙️ VCP SETTINGS 
// ==========================================
target_points = input.float(30.0, title="🎯 VCP Target Points (Rs)")
sl_buffer     = input.float(2.0, title="🛑 VCP SL Buffer (Rs)")

// ==========================================
// 🚀 VCP 5-MIN INTRADAY ENGINE
// ==========================================
// Time Filter
h = hour(time, "Asia/Kolkata")
m = minute(time, "Asia/Kolkata")
current_time = h * 100 + m
in_session = (current_time >= 930) and (current_time <= 1100)

// Daily Reset & Trade Counter
var float vcp_day_open = na
var int trades_today = 0

if session.isfirstbar_regular
    vcp_day_open := open
    trades_today := 0

if strategy.position_size != 0 and strategy.position_size[1] == 0
    trades_today += 1

can_trade = (trades_today == 0) and (strategy.position_size == 0)

// Trend & Candle Logic
vcp_bull_trend = close > vcp_day_open
vcp_bear_trend = close < vcp_day_open

vcp_red = close < open
vcp_green = close > open

bull_setup = vcp_bull_trend and vcp_red and vcp_red[1] and (volume < volume[1]) and in_session and can_trade
bear_setup = vcp_bear_trend and vcp_green and vcp_green[1] and (volume < volume[1]) and in_session and can_trade

var float ep = na
var float sl = na
var float tp = na

if bull_setup
    ep := high
    sl := low - sl_buffer
    tp := ep + target_points
    strategy.entry("Buy", strategy.long, stop=ep)
    strategy.exit("Exit Buy", "Buy", stop=sl, limit=tp)

if bear_setup
    ep := low
    sl := high + sl_buffer
    tp := ep - target_points
    strategy.entry("Sell", strategy.short, stop=ep)
    strategy.exit("Exit Sell", "Sell", stop=sl, limit=tp)

if not in_session and strategy.position_size == 0
    strategy.cancel_all()

plotshape(bull_setup, title="VCP Bullish Entry", text="BUY", style=shape.triangleup, location=location.belowbar, color=color.new(color.green, 0), size=size.small)
plotshape(bear_setup, title="VCP Bearish Entry", text="SELL", style=shape.triangledown, location=location.abovebar, color=color.new(color.red, 0), size=size.small)


// ==========================================
// 🧱 90-DAY SUPPORT & RESISTANCE ENGINE
// ==========================================
// Daily time frame par pichle 90 din ka High aur Low nikalna
get_90d_snr() =>
    res = ta.highest(high[1], 90)
    sup = ta.lowest(low[1], 90)
    [res, sup]

[res_90d, sup_90d] = request.security(syminfo.tickerid, "D", get_90d_snr(), lookahead = barmerge.lookahead_off)

// Chart par S&R Lines aur Labels plot karna
var line line_res = na
var line line_sup = na
var label lbl_res = na
var label lbl_sup = na

if barstate.islast
    if not na(line_res)
        line.delete(line_res)
    if not na(lbl_res)
        label.delete(lbl_res)
        
    line_res := line.new(bar_index - 1, res_90d, bar_index, res_90d, color=color.rgb(239, 83, 80), width=2, style=line.style_solid, extend=extend.both)
    lbl_res  := label.new(bar_index + 4, res_90d, "90D RESISTANCE: " + str.tostring(res_90d, "#.##"), color=color.rgb(239, 83, 80), textcolor=color.white, style=label.style_label_left, size=size.small)

    if not na(line_sup)
        line.delete(line_sup)
    if not na(lbl_sup)
        label.delete(lbl_sup)
        
    line_sup := line.new(bar_index - 1, sup_90d, bar_index, sup_90d, color=color.rgb(38, 166, 154), width=2, style=line.style_solid, extend=extend.both)
    lbl_sup  := label.new(bar_index + 4, sup_90d, "90D SUPPORT: " + str.tostring(sup_90d, "#.##"), color=color.rgb(38, 166, 154), textcolor=color.white, style=label.style_label_left, size=size.small)


// ==========================================
// 📊 SMALL P/L TABLE (Neat & Clean)
// ==========================================
var table pl_table = table.new(position.top_right, 2, 4, border_width=1, border_color=color.gray)
if barstate.islast
    table.cell(pl_table, 0, 0, "VCP Strategy", bgcolor=color.blue, text_color=color.white)
    table.cell(pl_table, 1, 0, "Stats", bgcolor=color.blue, text_color=color.white)
    
    table.cell(pl_table, 0, 1, "Target Set", bgcolor=color.gray, text_color=color.white)
    table.cell(pl_table, 1, 1, str.tostring(target_points) + " Pts", bgcolor=color.black, text_color=color.white)
    
    table.cell(pl_table, 0, 2, "Net Profit (₹)", bgcolor=color.gray, text_color=color.white)
    table.cell(pl_table, 1, 2, str.tostring(strategy.netprofit, "#.##"), bgcolor=strategy.netprofit > 0 ? color.green : color.red, text_color=color.white)
