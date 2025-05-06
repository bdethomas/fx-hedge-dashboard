import streamlit as st
import pandas as pd

# ----------------------------------------
# Helper function: compute the blended forward price
# ----------------------------------------
def calc_hedge(df: pd.DataFrame, spot_rate: float):
    df = df.copy()
    # Calculate outright forward rates
    df['Outright']     = spot_rate + df['ForwardPts']
    # Total notional and guard against zero
    total_notional     = df['Notional'].sum()
    if total_notional == 0:
        raise ValueError("Total notional is zero. Enter at least one positive Notional.")
    # Weights and contributions
    df['Weight']       = df['Notional'] / total_notional
    df['Contribution'] = df['Outright'] * df['Weight']
    # Blended forward price
    blended = df['Contribution'].sum()
    return blended, df

# ----------------------------------------
# Page config & header
# ----------------------------------------
st.set_page_config(page_title="FX Hedge Calculator", layout="wide")
st.title("🛡️ Client Exposure Hedge Calculator")

# ----------------------------------------
# Sidebar inputs
# ----------------------------------------
st.sidebar.header("Inputs")
uploaded = st.sidebar.file_uploader("1) Upload exposures CSV", type=["csv"])
spot     = st.sidebar.number_input("2) Spot Rate", value=1.000000, format="%.6f")

# ----------------------------------------
# Main area
# ----------------------------------------
if not uploaded:
    st.info("Please upload a CSV with columns: Expiry, Notional, ForwardPts, ClientDirection")
else:
    try:
        df = pd.read_csv(uploaded, parse_dates=['Expiry'])
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
    else:
        # Validate required columns
        required = {'Expiry', 'Notional', 'ForwardPts', 'ClientDirection'}
        missing  = required - set(df.columns)
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
        else:
            # Derive bank trade direction by flipping client intent
            df['TradeDirection'] = df['ClientDirection'].apply(
                lambda x: 'Buy EUR' if 'Sell EUR' in x else 'Sell EUR'
            )
            try:
                blended, result = calc_hedge(df, spot)
            except Exception as e:
                st.error(f"Calculation error: {e}")
            else:
                # Display blended price
                st.metric("Blended Hedge Price", f"{blended:.6f}")
                # Show client exposures including their intended direction
                st.markdown("#### Client Exposures")
                st.table(result[['Expiry','ClientDirection','Notional','ForwardPts']])
                # Build and show bank trade instructions
                trade_df = result[['Expiry','TradeDirection','Notional','Outright']].copy()
                trade_df.rename(columns={'TradeDirection':'Direction','Outright':'Rate'}, inplace=True)
                st.markdown("#### Trade Instructions")
                st.table(trade_df)
                # Per-expiry contributions chart
                st.markdown("#### Per-expiry Contributions")
                st.bar_chart(
                    result.set_index('Expiry')['Contribution'],
                    use_container_width=True
                )
