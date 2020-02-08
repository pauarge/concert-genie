import React from 'react';
import BpkButton from 'bpk-component-button';
import BpkInput, {INPUT_TYPES} from 'bpk-component-input';
import {colors} from 'bpk-tokens/tokens/base.es6';
import {withButtonAlignment} from "bpk-component-icon";
import LongArrowRightIconSm from "bpk-component-icon/sm/long-arrow-right";
import BpkSectionList from "bpk-component-section-list";
import BpkSectionListSection from "bpk-component-section-list/src/BpkSectionListSection";
import BpkSectionListItem from "bpk-component-section-list/src/BpkSectionListItem";

const AlignedArrow = withButtonAlignment(LongArrowRightIconSm);

class Search extends React.Component {
  constructor(props) {
    super(props);
    this.state = {value: '', results: []};

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event) {
    this.setState({value: event.target.value});
  }

  handleSubmit(event) {
    event.preventDefault();
    fetch("http://localhost:5000/?artist=" + this.state.value)
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            results: result,
          });
        },
        // Note: it's important to handle errors here
        // instead of a catch() block so that we don't swallow
        // exceptions from actual bugs in components.
        (error) => {
          console.log(error);
        }
      )
  }

  render() {
    return (
      <>
        <form onSubmit={this.handleSubmit}>
          <p>
            <BpkInput
              id="origin"
              type={INPUT_TYPES.text}
              name="origin"
              placeholder="Artist"
              value={this.state.value}
              onChange={this.handleChange}
            />
          </p>
          <p>
            <BpkButton submit={true}>
              Search&nbsp;
              <AlignedArrow fill={colors.colorWhite}/>
            </BpkButton>
          </p>
        </form>
        {this.state.results.length > 0 &&
        <p>
          <BpkSectionList>
            <BpkSectionListSection headerText="Songs">
              {this.state.results.map(i => <BpkSectionListItem>{i}</BpkSectionListItem>)}
            </BpkSectionListSection>
          </BpkSectionList>
        </p>}
      </>);
  }
}

export default Search;
